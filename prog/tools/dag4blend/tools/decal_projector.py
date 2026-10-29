"""Project cursor-aligned decals onto evaluated mesh triangles with box/convex clipping."""
import json
import math
from pathlib import Path

import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.view3d_utils import region_2d_to_origin_3d, region_2d_to_vector_3d

from .authoring import evaluated_mesh

_active_handlers = []


def resolve_decal_settings(image, library_path, shape, entry):
    bounds, convex = (0, 0, 1, 1), None
    if library_path:
        path = Path(bpy.path.abspath(library_path))
        library = json.loads(path.read_text(encoding='utf8'))
        item = library[shape][entry]
        if shape == 'rectangles':
            bounds = item
        else:
            convex = item
            bounds = (min(u for u, v in item), min(v for u, v in item),
                      max(u for u, v in item), max(v for u, v in item))
        if not image and library.get('texture'):
            image = str(path.parent / library['texture'])
    if image and not Path(bpy.path.abspath(image)).is_file():
        raise ValueError('Decal texture file does not exist')
    return bounds, convex, image


def clip_polygon(vertices, normal, distance):
    if not vertices:
        return []
    result = []
    previous = vertices[-1]
    previous_distance = normal.dot(previous[0]) + distance
    for current in vertices:
        current_distance = normal.dot(current[0]) + distance
        if (current_distance >= 0) != (previous_distance >= 0):
            fraction = previous_distance / (previous_distance - current_distance)
            result.append((previous[0].lerp(current[0], fraction),
                           previous[1].lerp(current[1], fraction)))
        if current_distance >= 0:
            result.append(current)
        previous, previous_distance = current, current_distance
    return result


def project_decal(context, target, width, height, depth, offset=0.001,
                  bounds=(0, 0, 1, 1), convex=None, front_only=True, image_path='', matrix=None):
    if min(width, height, depth) <= 0:
        raise ValueError('Projection width, height and depth must be positive')
    u0, v0, u1, v1 = bounds
    if u1 <= u0 or v1 <= v0:
        raise ValueError('Invalid decal UV bounds')
    matrix = matrix.copy() if matrix is not None else context.scene.cursor.matrix.copy()
    vertices, faces, normals = [], [], []
    planes = [(Vector((1, 0, 0)), width / 2), (Vector((-1, 0, 0)), width / 2),
              (Vector((0, 1, 0)), height / 2), (Vector((0, -1, 0)), height / 2),
              (Vector((0, 0, 1)), depth / 2), (Vector((0, 0, -1)), depth / 2)]
    if convex:
        polygon = [Vector(((u - u0) / (u1 - u0) * width - width / 2,
                           (v - v0) / (v1 - v0) * height - height / 2, 0)) for u, v in convex]
        if len(polygon) < 3:
            raise ValueError('Convex decal needs at least three points')
        area = sum(a.x * b.y - b.x * a.y for a, b in zip(polygon, polygon[1:] + polygon[:1]))
        if area < 0:
            polygon.reverse()
        for a, b in zip(polygon, polygon[1:] + polygon[:1]):
            normal = Vector((a.y - b.y, b.x - a.x, 0))
            planes.append((normal, -normal.dot(a)))
    image = bpy.data.images.load(bpy.path.abspath(image_path), check_existing=True) if image_path else None
    source = evaluated_mesh(context, target)
    try:
        source.calc_loop_triangles()
        transform = matrix.inverted() @ target.matrix_world
        normal_transform = transform.inverted().transposed().to_3x3()
        for triangle in source.loop_triangles:
            points = [transform @ source.vertices[index].co for index in triangle.vertices]
            if front_only and (points[1] - points[0]).cross(points[2] - points[0]).z <= 0:
                continue
            polygon = [(point, (normal_transform @ source.corner_normals[loop].vector).normalized())
                       for point, loop in zip(points, triangle.loops)]
            for normal, distance in planes:
                polygon = clip_polygon(polygon, normal, distance)
            if len(polygon) < 3:
                continue
            start = len(vertices)
            vertices.extend(point + normal.normalized() * offset for point, normal in polygon)
            normals.extend(normal.normalized() for point, normal in polygon)
            faces.append(tuple(range(start, len(vertices))))
    finally:
        bpy.data.meshes.remove(source)
    if not faces:
        raise ValueError('No target faces intersect the cursor projection volume')
    mesh = bpy.data.meshes.new(target.name + '_decal')
    mesh.from_pydata(vertices, [], faces)
    uv = mesh.uv_layers.new(name='UVMap')
    for loop, data in zip(mesh.loops, uv.data):
        co = mesh.vertices[loop.vertex_index].co
        # Offset normal displacement must not shift the projected UV mapping.
        co = co - normals[loop.vertex_index] * offset
        data.uv = (u0 + (co.x / width + 0.5) * (u1 - u0),
                   v0 + (co.y / height + 0.5) * (v1 - v0))
    mesh.normals_split_custom_set([normals[loop.vertex_index] for loop in mesh.loops])
    obj = bpy.data.objects.new(mesh.name, mesh)
    context.collection.objects.link(obj)
    obj.matrix_world = matrix
    if image is not None:
        material = bpy.data.materials.new(Path(image_path).stem + '_decal')
        material.use_nodes = True
        bsdf = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        texture = material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image = image
        material.node_tree.links.new(texture.outputs['Color'], bsdf.inputs['Base Color'])
        material.node_tree.links.new(texture.outputs['Alpha'], bsdf.inputs['Alpha'])
        mesh.materials.append(material)
    return obj


class DAGOR_OT_Project_Decal(bpy.types.Operator):
    bl_idname = 'dt.project_decal'
    bl_label = 'Project Decal at Cursor'
    bl_description = 'Use the 3D cursor position and rotation to project onto the target mesh'
    bl_options = {'REGISTER', 'UNDO'}
    target_name: StringProperty(name='Target mesh')
    width: FloatProperty(name='Width', default=1, min=0.001)
    height: FloatProperty(name='Height', default=1, min=0.001)
    depth: FloatProperty(name='Depth', default=1, min=0.001)
    offset: FloatProperty(name='Surface offset', default=0.001, min=0)
    front_only: BoolProperty(name='Front faces only', default=True)
    interactive: BoolProperty(name='Place interactively in viewport', default=False)
    image_path: StringProperty(name='Texture', subtype='FILE_PATH')
    library: StringProperty(name='Decal JSON library', subtype='FILE_PATH')
    shape: EnumProperty(items=[('rectangles', 'Rectangle', 'Use a rectangular atlas entry'),
                               ('convexes', 'Convex', 'Use a convex atlas entry')])
    entry: IntProperty(name='Library entry (zero-based)', default=0, min=0)

    def invoke(self, context, event):
        if context.active_object and context.active_object.type == 'MESH':
            self.target_name = context.active_object.name
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop_search(self, 'target_name', bpy.data, 'objects')
        for name in ('width', 'height', 'depth', 'offset', 'front_only', 'interactive',
                     'image_path', 'library', 'shape', 'entry'):
            self.layout.prop(self, name)

    def execute(self, context):
        target = bpy.data.objects.get(self.target_name)
        if target is None or target.type != 'MESH':
            self.report({'ERROR'}, 'Choose a mesh target')
            return {'CANCELLED'}
        bounds, convex, image = (0, 0, 1, 1), None, self.image_path
        try:
            if self.interactive:
                settings = resolve_decal_settings(self.image_path, self.library, self.shape, self.entry)
                return self.begin_placement(context, target, settings)
            if image and not Path(bpy.path.abspath(image)).is_file():
                raise ValueError('Decal texture file does not exist')
            if self.library:
                path = Path(bpy.path.abspath(self.library))
                library = json.loads(path.read_text(encoding='utf8'))
                item = library[self.shape][self.entry]
                if self.shape == 'rectangles':
                    bounds = item
                else:
                    convex = item
                    bounds = (min(u for u, v in item), min(v for u, v in item),
                              max(u for u, v in item), max(v for u, v in item))
                if not image and library.get('texture'):
                    image = str(path.parent / library['texture'])
            obj = project_decal(context, target, self.width, self.height, self.depth,
                                self.offset, bounds, convex, self.front_only, image)
        except (ValueError, RuntimeError, OSError, KeyError, IndexError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {'FINISHED'}

    def begin_placement(self, context, target, settings):
        if context.area is None or context.area.type != 'VIEW_3D':
            raise ValueError('Interactive decal placement requires a 3D viewport')
        self._region = next(region for region in context.area.regions if region.type == 'WINDOW')
        self._view = context.area.spaces.active.region_3d
        source = evaluated_mesh(context, target)
        try:
            source.calc_loop_triangles()
            self._tree = BVHTree.FromPolygons([target.matrix_world @ vert.co for vert in source.vertices],
                [triangle.vertices for triangle in source.loop_triangles], all_triangles=True)
        finally:
            bpy.data.meshes.remove(source)
        self._settings, self._area = settings, context.area
        self._matrix, self._mouse, self._angle, self._placed = None, None, 0.0, 0
        self._handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_preview, (), 'WINDOW', 'POST_VIEW')
        _active_handlers.append((self._handler, self._area))
        context.area.header_text_set('LMB: place | Shift + move: scale | Ctrl + move: rotate | RMB / Esc: finish')
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def draw_preview(self):
        if self._matrix is None:
            return
        import gpu
        from gpu_extras.batch import batch_for_shader
        points = [self._matrix @ Vector((x * self.width / 2, y * self.height / 2, self.offset))
                  for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        points = [points[index] for index in (0, 1, 1, 2, 2, 3, 3, 0)]
        shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINES', {'pos': points})
        shader.bind()
        shader.uniform_float('color', (1, 0.65, 0.1, 1))
        batch.draw(shader)

    def finish_placement(self):
        if (self._handler, self._area) in _active_handlers:
            bpy.types.SpaceView3D.draw_handler_remove(self._handler, 'WINDOW')
            _active_handlers.remove((self._handler, self._area))
        try:
            self._area.header_text_set(None)
            self._area.tag_redraw()
        except ReferenceError:
            pass
        return {'FINISHED'} if self._placed else {'CANCELLED'}

    def cancel(self, context):
        if hasattr(self, '_handler'):
            self.finish_placement()

    def modal(self, context, event):
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            return self.finish_placement()
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}
        target = bpy.data.objects.get(self.target_name)
        if target is None:
            return self.finish_placement()
        if event.type == 'MOUSEMOVE':
            mouse = (event.mouse_x - self._region.x, event.mouse_y - self._region.y)
            if self._mouse is not None:
                if event.shift:
                    factor = math.exp(max(-1, min(1, (mouse[1] - self._mouse[1]) * 0.01)))
                    self.width = max(0.001, min(10000, self.width * factor))
                    self.height = max(0.001, min(10000, self.height * factor))
                if event.ctrl:
                    self._angle += (mouse[0] - self._mouse[0]) * 0.01
            self._mouse = mouse
            origin = region_2d_to_origin_3d(self._region, self._view, mouse)
            direction = region_2d_to_vector_3d(self._region, self._view, mouse)
            position, normal, _, _ = self._tree.ray_cast(origin, direction)
            self._matrix = None
            if position is not None:
                self._matrix = normal.to_track_quat('Z', 'Y').to_matrix().to_4x4() @ Matrix.Rotation(self._angle, 4, 'Z')
                self._matrix.translation = position
            self._area.tag_redraw()
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS' and self._matrix is not None:
            bounds, convex, image = self._settings
            try:
                project_decal(context, target, self.width, self.height, self.depth, self.offset,
                              bounds, convex, self.front_only, image, self._matrix)
                self._placed += 1
            except (ValueError, RuntimeError, OSError) as error:
                self.report({'WARNING'}, str(error))
        return {'RUNNING_MODAL'}


class DAGOR_PT_Decals(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Decal Projector'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.label(text='Align the 3D cursor to the surface')
        self.layout.operator('dt.project_decal')


classes = (DAGOR_OT_Project_Decal, DAGOR_PT_Decals)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for handler, area in list(_active_handlers):
        bpy.types.SpaceView3D.draw_handler_remove(handler, 'WINDOW')
        try:
            area.header_text_set(None)
        except ReferenceError:
            pass
    _active_handlers.clear()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
