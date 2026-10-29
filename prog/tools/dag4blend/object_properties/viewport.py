"""Fast property inspection and material/vertex-color viewport controls."""
import blf
import bpy
from bpy.props import EnumProperty
from bpy_extras.view3d_utils import location_3d_to_region_2d

from .codec import serialize_properties

_handler = None


def draw_properties():
    context = bpy.context
    if context.region is None or context.region_data is None:
        return
    blf.size(0, 12)
    blf.color(0, 1, 1, 1, 1)
    for obj in list(context.selected_objects)[:20]:
        position = location_3d_to_region_2d(context.region, context.region_data, obj.matrix_world.translation)
        if position is None:
            continue
        lines = [obj.name] + serialize_properties(dict(obj.dagorprops.items())).splitlines()
        for index, line in enumerate(lines):
            blf.position(0, position.x + 8, position.y - index * 15, 0)
            blf.draw(0, line)


class DAGOR_OT_Property_Overlay(bpy.types.Operator):
    bl_idname = 'dt.property_overlay'
    bl_label = 'Toggle Properties in Viewport'

    def execute(self, context):
        global _handler
        if _handler is None:
            _handler = bpy.types.SpaceView3D.draw_handler_add(draw_properties, (), 'WINDOW', 'POST_PIXEL')
        else:
            bpy.types.SpaceView3D.draw_handler_remove(_handler, 'WINDOW')
            _handler = None
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        return {'FINISHED'}


class DAGOR_OT_Viewport_Display(bpy.types.Operator):
    bl_idname = 'dt.viewport_display'
    bl_label = 'Dagor Viewport Display'
    mode: EnumProperty(items=[('VERTEX', 'Vertex Colors', 'Show the active color layer'),
                              ('MATERIAL', 'Solid Materials', 'Show material colors'),
                              ('TEXTURE', 'Texture Preview', 'Show material node-tree textures')])

    def execute(self, context):
        for obj in context.selected_objects:
            obj.display_type = 'TEXTURED' if self.mode == 'TEXTURE' else 'SOLID'
        for window in context.window_manager.windows:
            for area in window.screen.areas:
                if area.type != 'VIEW_3D':
                    continue
                shading = area.spaces.active.shading
                shading.type = 'MATERIAL' if self.mode == 'TEXTURE' else 'SOLID'
                if self.mode != 'TEXTURE':
                    shading.color_type = self.mode
                area.tag_redraw()
        return {'FINISHED'}


class DAGOR_PT_Fast_Properties(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Fast User Properties'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        row = self.layout.row(align=True)
        for operation, text in [('COPY', 'Copy'), ('PASTE', 'Paste'), ('CLEAR', 'Clear')]:
            row.operator('dt.property_clipboard', text=text).operation = operation
        self.layout.operator('dt.property_overlay', depress=_handler is not None)
        for mode, text in [('VERTEX', 'Show Vertex Colors'), ('MATERIAL', 'Show Solid Materials'),
                            ('TEXTURE', 'Show Textures')]:
            self.layout.operator('dt.viewport_display', text=text).mode = mode
        for obj in list(context.selected_objects)[:20]:
            box = self.layout.box()
            box.label(text=obj.name)
            for line in serialize_properties(dict(obj.dagorprops.items())).splitlines():
                box.label(text=line)


classes = (DAGOR_OT_Property_Overlay, DAGOR_OT_Viewport_Display, DAGOR_PT_Fast_Properties)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    global _handler
    if _handler is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_handler, 'WINDOW')
        _handler = None
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
