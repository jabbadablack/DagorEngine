"""Dagor Utility UV channel operations (channels are numbered from one)."""
import bpy
from bpy.props import EnumProperty, IntProperty
from bpy.types import Operator, Panel

_uv_buffer = None


def mesh_topology(mesh):
    return (len(mesh.vertices), tuple(loop.vertex_index for loop in mesh.loops),
            tuple((poly.loop_start, poly.loop_total) for poly in mesh.polygons))


def read_uv(layer):
    return [tuple(loop.uv) for loop in layer.data]


def write_uv(layer, values):
    for loop, value in zip(layer.data, values):
        loop.uv = value


def transfer_uv(mesh, source, destination, operation):
    """Copy coordinates without renaming channels used by material nodes."""
    layers = mesh.uv_layers
    if source > len(layers):
        raise ValueError(f'{mesh.name}: source channel {source} does not exist')
    if operation == 'REMOVE':
        layers.remove(layers[source - 1])
        return
    if source == destination:
        raise ValueError('Choose different source and destination channels')
    if operation == 'SWAP' and destination > len(layers):
        raise ValueError(f'{mesh.name}: destination channel {destination} does not exist')
    values = read_uv(layers[source - 1])
    while len(layers) < destination:
        layers.new(name='UVMap', do_init=False)
    if operation == 'SWAP':
        write_uv(layers[source - 1], read_uv(layers[destination - 1]))
    write_uv(layers[destination - 1], values)
    if operation == 'MOVE':
        layers.remove(layers[source - 1])
    mesh.update()


class DAGOR_OT_UV_Channel(Operator):
    bl_idname = 'dt.uv_channel'
    bl_label = 'UV Channels'
    bl_description = 'Copy, swap, move, or delete UV channels on selected meshes'
    bl_options = {'REGISTER', 'UNDO'}

    operation: EnumProperty(name='Operation', items=[
        ('COPY', 'Copy', 'Copy source coordinates to destination'),
        ('SWAP', 'Swap', 'Exchange coordinates between existing channels'),
        ('MOVE', 'Move', 'Copy coordinates to destination and remove source'),
        ('REMOVE', 'Delete', 'Remove source channel')])
    source: IntProperty(name='Source channel', default=1, min=1, max=8)
    destination: IntProperty(name='Destination channel', default=2, min=1, max=8)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and any(
            obj.type == 'MESH' and obj.data.is_editable for obj in context.selected_objects)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'operation')
        self.layout.prop(self, 'source')
        if self.operation != 'REMOVE':
            self.layout.prop(self, 'destination')

    def execute(self, context):
        meshes = {obj.data for obj in context.selected_objects
                  if obj.type == 'MESH' and obj.data.is_editable}
        # Validate the whole selection before modifying shared mesh data.
        for mesh in meshes:
            if self.source > len(mesh.uv_layers):
                self.report({'ERROR'}, f'{mesh.name}: source channel does not exist')
                return {'CANCELLED'}
            if self.operation != 'REMOVE' and self.source == self.destination:
                self.report({'ERROR'}, 'Choose different source and destination channels')
                return {'CANCELLED'}
            if self.operation == 'SWAP' and self.destination > len(mesh.uv_layers):
                self.report({'ERROR'}, f'{mesh.name}: destination channel does not exist')
                return {'CANCELLED'}
        for mesh in meshes:
            transfer_uv(mesh, self.source, self.destination, self.operation)
        self.report({'INFO'}, f'Updated UV channels on {len(meshes)} meshes')
        return {'FINISHED'}


class DAGOR_PT_UV_Channels(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_label = 'UV Channels'
    bl_context = 'objectmode'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        for operation, label in [('COPY', 'Copy'), ('SWAP', 'Swap'),
                                 ('MOVE', 'Move'), ('REMOVE', 'Delete')]:
            self.layout.operator('dt.uv_channel', text=label).operation = operation
        self.layout.separator()
        self.layout.operator('dt.uv_buffer', text='Copy Buffer').operation = 'COPY'
        row = self.layout.row()
        row.enabled = _uv_buffer is not None
        row.operator('dt.uv_buffer', text='Paste Buffer').operation = 'PASTE'


class DAGOR_OT_UV_Buffer(Operator):
    bl_idname = 'dt.uv_buffer'
    bl_label = 'UV Buffer'
    bl_description = 'Transfer UV coordinates between meshes with matching indexed topology'
    bl_options = {'REGISTER', 'UNDO'}
    operation: EnumProperty(items=[('COPY', 'Copy', 'Copy from active mesh'),
                                   ('PASTE', 'Paste', 'Paste to selected meshes')])
    channel: IntProperty(name='UV channel', default=1, min=1, max=8)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and context.active_object is not None and context.active_object.type == 'MESH'

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        global _uv_buffer
        if self.operation == 'COPY':
            mesh = context.active_object.data
            if self.channel > len(mesh.uv_layers):
                self.report({'ERROR'}, 'Source channel does not exist')
                return {'CANCELLED'}
            _uv_buffer = (mesh_topology(mesh), read_uv(mesh.uv_layers[self.channel - 1]))
        else:
            if _uv_buffer is None:
                self.report({'ERROR'}, 'UV buffer is empty')
                return {'CANCELLED'}
            meshes = {obj.data for obj in context.selected_objects
                      if obj.type == 'MESH' and obj.data.is_editable}
            if not meshes:
                return {'CANCELLED'}
            topology, values = _uv_buffer
            if any(mesh_topology(mesh) != topology for mesh in meshes):
                self.report({'ERROR'}, 'All targets must match the buffered vertex order and face topology')
                return {'CANCELLED'}
            for mesh in meshes:
                while len(mesh.uv_layers) < self.channel:
                    mesh.uv_layers.new(name='UVMap', do_init=False)
                write_uv(mesh.uv_layers[self.channel - 1], values)
                mesh.update()
        return {'FINISHED'}


classes = (DAGOR_OT_UV_Channel, DAGOR_OT_UV_Buffer, DAGOR_PT_UV_Channels)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _uv_buffer
    _uv_buffer = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
