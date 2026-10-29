"""Pivot Painter data for render/shaders/pivot_painter.dshl (32x64, four levels)."""
import os
from pathlib import Path
import struct
import tempfile

import bpy
from bpy.props import IntProperty, StringProperty
from mathutils import Vector

from .authoring import evaluated_mesh

WIDTH, HEIGHT, MAX_LEVELS, EXTENT = 32, 64, 4, 20.48


def encode_dds(pixels, half_float):
    if len(pixels) != WIDTH * HEIGHT:
        raise ValueError('Pivot Painter textures must contain exactly 2048 pixels')
    pixel_size = 8 if half_float else 4
    # DDS_HEADER with a DX10 pixel-format extension. Pitch is bytes per row.
    header = struct.pack('<7I11I8I5I', 124, 0x100F, HEIGHT, WIDTH, WIDTH * pixel_size, 0, 0,
                         *([0] * 11), 32, 4, int.from_bytes(b'DX10', 'little'), 0, 0, 0, 0, 0,
                         0x1000, 0, 0, 0, 0)
    dx10 = struct.pack('<5I', 10 if half_float else 28, 3, 0, 1, 0)
    if half_float:
        data = b''.join(struct.pack('<4e', *pixel) for pixel in pixels)
    else:
        data = bytes(round(max(0, min(1, value)) * 255) for pixel in pixels for value in pixel)
    return b'DDS ' + header + dx10 + data


def hierarchy_data(root):
    nodes = []

    def visit(obj, depth):
        if obj.type not in {'MESH', 'EMPTY'}:
            for child in sorted(obj.children, key=lambda child: child.name):
                visit(child, depth)
            return
        if depth >= MAX_LEVELS:
            raise ValueError('Pivot Painter supports at most four hierarchy levels')
        nodes.append(obj)
        for child in sorted(obj.children, key=lambda child: child.name):
            visit(child, depth + 1)

    visit(root, 0)
    if not nodes or not any(obj.type == 'MESH' for obj in nodes):
        raise ValueError('Choose a hierarchy containing branch meshes')
    if len(nodes) > WIDTH * HEIGHT:
        raise ValueError('Pivot Painter supports at most 2048 hierarchy nodes')
    indices = {obj: index for index, obj in enumerate(nodes)}
    inverse = root.matrix_world.inverted()
    positions = [(0, 0, 0, 0)] * (WIDTH * HEIGHT)
    directions = [(0.5, 1, 0.5, 0)] * (WIDTH * HEIGHT)
    for obj, index in indices.items():
        parent = obj.parent
        while parent is not None and parent not in indices:
            parent = parent.parent
        parent_index = indices[parent] if parent in indices else index
        tm = inverse @ obj.matrix_world
        pivot = tm.translation
        # Branch local +Z is the growth direction. Exported model coordinates
        # use Dagor's Y-up basis, as do the corresponding texture vectors.
        direction = (tm.to_3x3() @ Vector((0, 0, 1))).normalized()
        extent = max(((tm @ Vector(corner) - pivot).dot(direction) for corner in obj.bound_box), default=0) if obj.type == 'MESH' else 0
        extent = max(extent, 0.001)
        if extent > EXTENT:
            raise ValueError(f'{obj.name}: branch extent exceeds the shader limit of {EXTENT}')
        positions[index] = (pivot.x, pivot.z, pivot.y, parent_index)
        directions[index] = (direction.x * 0.5 + 0.5, direction.z * 0.5 + 0.5,
                              direction.y * 0.5 + 0.5, extent / EXTENT)
    return nodes, indices, positions, directions


def paint_hierarchy(context, root, output_directory, channel=4):
    context.view_layer.update()
    nodes, indices, positions, directions = hierarchy_data(root)
    # Validate both binary outputs before creating geometry or writing files.
    encoded = (encode_dds(positions, True), encode_dds(directions, False))
    directory = Path(bpy.path.abspath(output_directory))
    directory.mkdir(parents=True, exist_ok=True)
    paths = [directory / 'pivot_pos.dds', directory / 'pivot_dir.dds']
    selected, active = list(context.selected_objects), context.view_layer.objects.active
    duplicates, temporary_meshes, result = [], [], None
    try:
        for node in nodes:
            if node.type != 'MESH':
                continue
            mesh = evaluated_mesh(context, node)
            temporary_meshes.append(mesh)
            duplicate = bpy.data.objects.new('Dagor pivot branch', mesh)
            context.collection.objects.link(duplicate)
            duplicate.matrix_world = node.matrix_world.copy()
            duplicates.append(duplicate)
            # Canonical names agree with the DAG exporter's channel sorting.
            for layer in mesh.uv_layers:
                layer.name = '_dagor_' + layer.name
            for index, layer in enumerate(mesh.uv_layers):
                layer.name = 'UVMap' if index == 0 else f'UVMap.{index:03d}'
            while len(mesh.uv_layers) < channel:
                mesh.uv_layers.new(name='UVMap', do_init=False)
            index = indices[node]
            # DAG mesh import flips V for the engine. Store the inverse here
            # so shader getIndexByUv addresses the DDS row index exactly.
            uv = ((index % WIDTH + 0.5) / WIDTH, 1 - (index // WIDTH + 0.5) / HEIGHT)
            for loop in mesh.uv_layers[channel - 1].data:
                loop.uv = uv
        anchor_mesh = bpy.data.meshes.new(root.name + '_wind')
        result = bpy.data.objects.new(anchor_mesh.name, anchor_mesh)
        context.collection.objects.link(result)
        result.matrix_world = root.matrix_world.copy()
        bpy.ops.object.select_all(action='DESELECT')
        context.view_layer.update()
        for obj in duplicates:
            obj.select_set(True)
        result.select_set(True)
        context.view_layer.objects.active = result
        bpy.ops.object.join()
        for path, payload in zip(paths, encoded):
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(dir=directory, delete=False, suffix='.dds.tmp') as output:
                    temporary = output.name
                    output.write(payload)
                os.replace(temporary, path)
                temporary = None
            finally:
                if temporary is not None:
                    os.unlink(temporary)
        result['dagor_pivot_position_texture'] = str(paths[0])
        result['dagor_pivot_direction_texture'] = str(paths[1])
        result['dagor_pivot_uv_channel'] = channel
        return result
    except Exception:
        # Remove only this operation's newly created objects and orphan meshes.
        for obj in duplicates + ([result] if result is not None else []):
            try:
                mesh = obj.data
                bpy.data.objects.remove(obj, do_unlink=True)
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            except ReferenceError:
                pass
        raise
    finally:
        for mesh in temporary_meshes:
            try:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            except ReferenceError:
                pass
        bpy.ops.object.select_all(action='DESELECT')
        for obj in selected:
            obj.select_set(True)
        context.view_layer.objects.active = active


class DAGOR_OT_Pivot_Painter(bpy.types.Operator):
    bl_idname = 'dt.pivot_painter'
    bl_label = 'Pivot Painter Vegetation'
    bl_description = 'Bake the active object hierarchy to a wind mesh and Dagor Pivot Painter DDS textures'
    bl_options = {'REGISTER', 'UNDO'}
    directory: StringProperty(name='Texture output directory', subtype='DIR_PATH', default='//')
    channel: IntProperty(name='Pivot UV channel', default=4, min=1, max=8)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        try:
            result = paint_hierarchy(context, context.active_object, self.directory, self.channel)
        except (ValueError, RuntimeError, OSError, OverflowError) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        self.report({'INFO'}, f'Created {result.name}; assign DDS textures to material slots 7 and 8')
        return {'FINISHED'}


class DAGOR_PT_Pivot_Painter(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Pivot Painter'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator('dt.pivot_painter')


classes = (DAGOR_OT_Pivot_Painter, DAGOR_PT_Pivot_Painter)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
