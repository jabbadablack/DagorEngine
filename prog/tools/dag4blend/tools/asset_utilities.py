"""Material conversion, deformation colors, UV atlas and normal orientation tools."""
import math

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty

from .authoring import selected_meshes
from .uv_tools import mesh_topology, read_uv, write_uv


def encode_deformation(base, deformed, configure_materials=True):
    if mesh_topology(base.data) != mesh_topology(deformed.data):
        raise ValueError('Base and deformed meshes must have identical indexed topology')
    if any(layer.name != 'DEFORM' for layer in base.data.color_attributes):
        raise ValueError('DEFORM must be the only color attribute for DAG color-channel export')
    transform = base.matrix_world.inverted() @ deformed.matrix_world
    # Match dag4blend's existing dynamic_deformed shape-key encoding.
    offsets = [a.co - transform @ b.co for a, b in zip(base.data.vertices, deformed.data.vertices)]
    distance = max((offset.length for offset in offsets), default=0)
    if base.data.users > 1:
        base.data = base.data.copy()
    mesh = base.data
    previous = mesh.color_attributes.get('DEFORM')
    if previous:
        mesh.color_attributes.remove(previous)
    color = mesh.color_attributes.new(name='DEFORM', type='FLOAT_COLOR', domain='CORNER')
    for loop, value in zip(mesh.loops, color.data):
        offset = offsets[loop.vertex_index]
        value.color_srgb = tuple(0.5 + component / (2 * distance) if distance else 0.5
                                 for component in offset) + (1,)
    mesh.color_attributes.active_color = color
    base['dagor_deform_max_height'] = 2 * distance
    if configure_materials:
        for material in mesh.materials:
            if material is not None:
                material.dagormat.shader_class = 'dynamic_deformed'
                material.dagormat.optional['max_height'] = 2 * distance
    return 2 * distance


def principled_inputs(material):
    color, texture = tuple(material.diffuse_color[:3]), ''
    if material.use_nodes:
        shader = next((node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED'), None)
        if shader:
            color = tuple(shader.inputs['Base Color'].default_value[:3])
            for link in shader.inputs['Base Color'].links:
                if link.from_node.type == 'TEX_IMAGE' and link.from_node.image:
                    texture = link.from_node.image.filepath or link.from_node.image.name
    return color, texture


def convert_material(material, to_dagor, shader):
    if to_dagor:
        color, texture = principled_inputs(material)
        converted = bpy.data.materials.new(material.name + '_dagor')
        converted.dagormat.diffuse = color
        converted.dagormat.shader_class = shader
        converted.dagormat.textures.tex0 = texture
    else:
        converted = bpy.data.materials.new(material.name + '_standard')
        converted.use_nodes = True
        bsdf = next(node for node in converted.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        bsdf.inputs['Base Color'].default_value = (*material.dagormat.diffuse, 1)
        texture = material.dagormat.textures.tex0
        if texture:
            image = bpy.data.images.get(texture)
            if image is None:
                try:
                    image = bpy.data.images.load(bpy.path.abspath(texture), check_existing=True)
                except RuntimeError:
                    image = bpy.data.images.get(texture.rsplit('/', 1)[-1].rsplit('\\', 1)[-1])
            if image:
                node = converted.node_tree.nodes.new('ShaderNodeTexImage')
                node.image = image
                converted.node_tree.links.new(node.outputs['Color'], bsdf.inputs['Base Color'])
    return converted


class DAGOR_OT_Deformation_Colors(bpy.types.Operator):
    bl_idname = 'dt.deformation_colors'
    bl_label = 'Vertex Position to Color'
    bl_description = 'Active mesh is the base; the other selected mesh is the deformed state'
    bl_options = {'REGISTER', 'UNDO'}
    configure_materials: BoolProperty(name='Configure dynamic_deformed materials', default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and len(selected_meshes(context)) == 2

    def execute(self, context):
        base = context.active_object
        meshes = selected_meshes(context)
        if base not in meshes:
            return {'CANCELLED'}
        deformed = next(obj for obj in meshes if obj != base)
        if any(layer.name != 'DEFORM' for layer in base.data.color_attributes):
            self.report({'ERROR'}, 'Use a base with DEFORM as its only color attribute to match DAG color-channel export')
            return {'CANCELLED'}
        try:
            height = encode_deformation(base, deformed, self.configure_materials)
        except ValueError as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        self.report({'INFO'}, f'Encoded deformation; max_height={height:g}')
        return {'FINISHED'}


class DAGOR_OT_Convert_Materials(bpy.types.Operator):
    bl_idname = 'dt.convert_materials'
    bl_label = 'Convert Materials'
    bl_description = 'Create converted copies and transfer diffuse color and directly connected diffuse textures'
    bl_options = {'REGISTER', 'UNDO'}
    to_dagor: BoolProperty(name='Convert to Dagor', default=True)
    shader: StringProperty(name='Dagor shader', default='rendinst_simple')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        converted = {}
        selected, active = list(context.selected_objects), context.view_layer.objects.active
        try:
            for obj in selected_meshes(context):
                if obj.data.users > 1:
                    obj.data = obj.data.copy()
                for slot in obj.material_slots:
                    material = slot.material
                    if material is None:
                        continue
                    if material not in converted:
                        converted[material] = convert_material(material, self.to_dagor, self.shader)
                    slot.material = converted[material]
        finally:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:
                obj.select_set(True)
            context.view_layer.objects.active = active
        return {'FINISHED'}


class DAGOR_OT_UV_Atlas(bpy.types.Operator):
    bl_idname = 'dt.uv_atlas'
    bl_label = 'Unwrap and Pack UV Atlas'
    bl_options = {'REGISTER', 'UNDO'}
    mode: EnumProperty(items=[('UNWRAP', 'Unwrap', 'Create angle-based UV charts'),
                              ('PACK', 'Pack', 'Repack existing charts without new cuts')])
    source: IntProperty(name='Source channel', default=1, min=1, max=8)
    target: IntProperty(name='Target channel', default=2, min=1, max=8)
    resolution: IntProperty(name='Texture size', default=1024, min=16, max=16384)
    padding: IntProperty(name='Gutter pixels', default=2, min=0, max=256)
    cut_angle: FloatProperty(name='Cut angle', default=math.radians(60), min=0, max=math.pi, subtype='ANGLE')
    preserve_seams: BoolProperty(name='Preserve marked seams', default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        targets = selected_meshes(context)
        if self.mode == 'PACK' and any(self.source > len(obj.data.uv_layers) for obj in targets):
            self.report({'ERROR'}, 'Every target must have the source UV channel')
            return {'CANCELLED'}
        selected, active = list(context.selected_objects), context.view_layer.objects.active
        try:
            for obj in targets:
                if obj.data.users > 1:
                    obj.data = obj.data.copy()
                mesh = obj.data
                values = read_uv(mesh.uv_layers[self.source - 1]) if self.mode == 'PACK' else None
                while len(mesh.uv_layers) < self.target:
                    mesh.uv_layers.new(name='UVMap', do_init=False)
                mesh.uv_layers.active_index = self.target - 1
                if values is not None:
                    write_uv(mesh.uv_layers[self.target - 1], values)
                else:
                    bm = bmesh.new()
                    try:
                        bm.from_mesh(mesh)
                        for edge in bm.edges:
                            keep = edge.seam and self.preserve_seams
                            edge.seam = keep or edge.is_boundary or (len(edge.link_faces) == 2
                                        and edge.calc_face_angle() >= self.cut_angle)
                        bm.to_mesh(mesh)
                    finally:
                        bm.free()
                bpy.ops.object.select_all(action='DESELECT')
                obj.select_set(True)
                context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.uv.select_all(action='SELECT')
                margin = self.padding / self.resolution
                if self.mode == 'UNWRAP':
                    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=margin)
                bpy.ops.uv.average_islands_scale()
                bpy.ops.uv.pack_islands(rotate=True, margin=margin, margin_method='FRACTION')
                bpy.ops.object.mode_set(mode='OBJECT')
        finally:
            if context.mode != 'OBJECT':
                bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected:
                obj.select_set(True)
            context.view_layer.objects.active = active
        return {'FINISHED'}


class DAGOR_OT_Fix_Normal_Orientation(bpy.types.Operator):
    bl_idname = 'dt.fix_normal_orientation'
    bl_label = 'Fix Normal Orientation'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def execute(self, context):
        for obj in selected_meshes(context):
            if obj.data.users > 1:
                obj.data = obj.data.copy()
            bm = bmesh.new()
            try:
                bm.from_mesh(obj.data)
                bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
                bm.to_mesh(obj.data)
            finally:
                bm.free()
            obj.data.update()
        return {'FINISHED'}


class DAGOR_PT_Asset_Utilities(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Asset Utilities'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator('dt.deformation_colors')
        self.layout.operator('dt.convert_materials', text='Standard to Dagor').to_dagor = True
        self.layout.operator('dt.convert_materials', text='Dagor to Standard').to_dagor = False
        self.layout.operator('dt.uv_atlas', text='Unwrap UV Atlas').mode = 'UNWRAP'
        self.layout.operator('dt.uv_atlas', text='Pack UV Atlas').mode = 'PACK'
        self.layout.operator('dt.fix_normal_orientation')


classes = (DAGOR_OT_Deformation_Colors, DAGOR_OT_Convert_Materials, DAGOR_OT_UV_Atlas,
           DAGOR_OT_Fix_Normal_Orientation, DAGOR_PT_Asset_Utilities)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
