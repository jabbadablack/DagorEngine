"""Deterministic CPU vertex/corner AO baking without renderer-specific materials."""
import math

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from .authoring import evaluated_mesh, selected_meshes


def occlusion_tree(context, objects):
    vertices, triangles = [], []
    for obj in objects:
        mesh = evaluated_mesh(context, obj)
        try:
            mesh.calc_loop_triangles()
            offset = len(vertices)
            vertices.extend(obj.matrix_world @ vert.co for vert in mesh.vertices)
            triangles.extend(tuple(index + offset for index in tri.vertices) for tri in mesh.loop_triangles)
        finally:
            bpy.data.meshes.remove(mesh)
    if not triangles:
        raise ValueError('No occluder geometry')
    return BVHTree.FromPolygons(vertices, triangles, all_triangles=True)


def sample_ao(tree, point, normal, samples, distance):
    normal = normal.normalized()
    axis = Vector((0, 0, 1)) if abs(normal.z) < 0.9 else Vector((1, 0, 0))
    tangent = normal.cross(axis).normalized()
    bitangent = normal.cross(tangent)
    origin = point + normal * max(1e-5, distance * 1e-5)
    hits = 0
    for index in range(samples):
        radius = math.sqrt((index + 0.5) / samples)
        angle = index * 2.399963229728653
        direction = (tangent * (radius * math.cos(angle)) + bitangent * (radius * math.sin(angle))
                     + normal * math.sqrt(1 - radius * radius))
        if tree.ray_cast(origin, direction, distance)[0] is not None:
            hits += 1
    return 1 - hits / samples


def bake_ao(context, targets, occluders, samples=64, distance=1.0, channel='RGB',
            light=(1, 1, 1), dark=(0, 0, 0), gradient=0.0, keep_material='', map_channel=8, output='MAP'):
    if map_channel == 0 and output == 'MAP':
        output = 'COLOR'
    tree = occlusion_tree(context, occluders)
    completed = 0
    context.window_manager.progress_begin(0, sum(len(obj.data.loops) for obj in targets))
    try:
        for obj in targets:
            evaluated = evaluated_mesh(context, obj)
            try:
                if len(evaluated.loops) != len(obj.data.loops) or len(evaluated.vertices) != len(obj.data.vertices):
                    raise ValueError(f'{obj.name}: apply topology-changing modifiers before baking vertex AO')
                if obj.data.users > 1:
                    obj.data = obj.data.copy()
                mesh = obj.data
                layer = (mesh.color_attributes.get('AO') if output == 'MAP' else
                         (mesh.color_attributes[0] if mesh.color_attributes else None))
                if layer is None:
                    layer = mesh.color_attributes.new(name='AO', type='FLOAT_COLOR', domain='CORNER')
                    for value in layer.data:
                        value.color_srgb = (1, 1, 1, 1)
                if output == 'MAP' and map_channel:
                    previous_map = mesh.attributes.get(f'dagor_map_{map_channel}')
                    if previous_map is not None:
                        if previous_map.data_type != 'FLOAT_VECTOR' or previous_map.domain != 'CORNER':
                            raise ValueError('AO map channel must be a corner vector attribute')
                        for index, loop in enumerate(mesh.loops):
                            color_index = index if layer.domain == 'CORNER' else loop.vertex_index
                            layer.data[color_index].color_srgb = (*previous_map.data[index].vector, 1)
                normal_matrix = obj.matrix_world.inverted().transposed().to_3x3()
                positions = [obj.matrix_world @ vert.co for vert in evaluated.vertices]
                low = min((point.z for point in positions), default=0)
                high = max((point.z for point in positions), default=0)
                results = {}
                for polygon in evaluated.polygons:
                    material = evaluated.materials[polygon.material_index] if polygon.material_index < len(evaluated.materials) else None
                    if keep_material and material is not None and material.name == keep_material:
                        continue
                    for loop_index in polygon.loop_indices:
                        loop = evaluated.loops[loop_index]
                        point = positions[loop.vertex_index]
                        normal = normal_matrix @ evaluated.corner_normals[loop_index].vector
                        value = sample_ao(tree, point, normal, samples, distance)
                        height = (point.z - low) / (high - low) if high > low else 1
                        value *= (1 - gradient) + gradient * height
                        color = tuple(a + (b - a) * value for a, b in zip(dark, light))
                        index = loop_index if layer.domain == 'CORNER' else loop.vertex_index
                        results.setdefault(index, []).append(color)
                        completed += 1
                        if completed % 512 == 0:
                            context.window_manager.progress_update(completed)
                components = range(3) if channel == 'RGB' else ({'R': 0, 'G': 1, 'B': 2}[channel],)
                for index, values in results.items():
                    previous = list(layer.data[index].color_srgb)
                    average = [sum(color[axis] for color in values) / len(values) for axis in range(3)]
                    for axis in components:
                        previous[axis] = average[axis]
                    previous[3] = 1
                    layer.data[index].color_srgb = previous
                mesh.color_attributes.active_color = layer
                if map_channel and output != 'COLOR':
                    name = f'dagor_map_{map_channel}'
                    attribute = mesh.attributes.get(name)
                    if attribute is None:
                        attribute = mesh.attributes.new(name=name, type='FLOAT_VECTOR', domain='CORNER')
                    if attribute.data_type != 'FLOAT_VECTOR' or attribute.domain != 'CORNER':
                        raise ValueError(f'{obj.name}: {name} must be a corner vector attribute')
                    for index, loop in enumerate(mesh.loops):
                        color_index = index if layer.domain == 'CORNER' else loop.vertex_index
                        attribute.data[index].vector = layer.data[color_index].color_srgb[:3]
                mesh.update()
            finally:
                bpy.data.meshes.remove(evaluated)
    finally:
        context.window_manager.progress_end()


class DAGOR_OT_Bake_Vertex_AO(bpy.types.Operator):
    bl_idname = 'dt.bake_vertex_ao'
    bl_label = 'Bake Vertex Ambient Occlusion'
    bl_options = {'REGISTER', 'UNDO'}
    samples: IntProperty(name='Hemisphere samples', default=64, min=8, max=512)
    distance: FloatProperty(name='Occlusion distance', default=1, min=0.001)
    scene_occluders: BoolProperty(name='Use visible scene geometry', default=False)
    channel: EnumProperty(name='Color channel', items=[('RGB', 'RGB', 'Write all color channels'),
        ('R', 'Red', 'Preserve green and blue'), ('G', 'Green', 'Preserve red and blue'),
        ('B', 'Blue', 'Preserve red and green')])
    light: FloatVectorProperty(name='Bright color', subtype='COLOR', size=3, default=(1, 1, 1), min=0, max=1)
    dark: FloatVectorProperty(name='Dark color', subtype='COLOR', size=3, default=(0, 0, 0), min=0, max=1)
    gradient: FloatProperty(name='Ground gradient strength', default=0, min=0, max=1)
    keep_material: StringProperty(name='Keep colors on material')
    map_channel: IntProperty(name='Engine map channel (0=color only)', default=8, min=0, max=10)
    output: EnumProperty(name='Output', items=[
        ('MAP', 'Engine Map and AO Preview', 'Preserve other color layers, including deformation and wind data'),
        ('COLOR', 'Vertex Colors', 'Write the first color layer'),
        ('BOTH', 'Engine Map and Vertex Colors', 'Write the map channel and replace first-layer vertex colors')])

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        targets = selected_meshes(context)
        occluders = ([obj for obj in context.scene.objects if obj.type == 'MESH' and obj.visible_get()]
                     if self.scene_occluders else targets)
        try:
            bake_ao(context, targets, occluders, self.samples, self.distance, self.channel,
                    self.light, self.dark, self.gradient, self.keep_material, self.map_channel, self.output)
        except (ValueError, RuntimeError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class DAGOR_PT_Vertex_AO(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Vertex AO'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator('dt.bake_vertex_ao')


classes = (DAGOR_OT_Bake_Vertex_AO, DAGOR_PT_Vertex_AO)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
