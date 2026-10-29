"""Editable Dagor scripts on armature bones, alongside preserved bind metadata."""
import bpy
from bpy.props import EnumProperty

from .codec import parse_properties, serialize_properties
from ..helpers.texts import get_text, show_text


def active_bone(context):
    pose = getattr(context, 'active_pose_bone', None)
    if pose is not None:
        return pose.bone
    return getattr(context, 'edit_bone', None) or getattr(context, 'bone', None)


class DAGOR_OT_Bone_Properties(bpy.types.Operator):
    bl_idname = 'dt.bone_properties'
    bl_label = 'Dagor Bone Properties'
    bl_options = {'REGISTER', 'UNDO'}
    operation: EnumProperty(items=[('COPY', 'Copy', 'Copy active bone script'),
        ('PASTE', 'Paste', 'Paste a script to selected bones'), ('CLEAR', 'Clear', 'Clear selected bone scripts'),
        ('OPEN', 'Open as Text', 'Edit the active bone script in a Text Editor'),
        ('APPLY', 'Apply from Text', 'Apply dagor_bone_properties text to selected bones')])

    @classmethod
    def poll(cls, context):
        return context.object is not None and context.object.type == 'ARMATURE' and active_bone(context) is not None

    def execute(self, context):
        bone = active_bone(context)
        if self.operation == 'COPY':
            context.window_manager.clipboard = bone.get('dagor_script', '')
            return {'FINISHED'}
        if self.operation == 'OPEN':
            text = get_text('dagor_bone_properties')
            text.clear()
            text.write(bone.get('dagor_script', ''))
            show_text(text, cursor_to_start=True)
            return {'FINISHED'}
        if self.operation == 'CLEAR':
            script = ''
        elif self.operation == 'PASTE':
            script = context.window_manager.clipboard
        else:
            text = bpy.data.texts.get('dagor_bone_properties')
            if text is None:
                self.report({'ERROR'}, 'Open the bone properties text before applying it')
                return {'CANCELLED'}
            script = text.as_string()
        script = serialize_properties(parse_properties(script))
        selected = getattr(context, 'selected_pose_bones', None)
        bones = [pose.bone for pose in selected] if selected else list(getattr(context, 'selected_editable_bones', None) or [])
        for target in bones or [bone]:
            target['dagor_script'] = script
        return {'FINISHED'}


class DAGOR_PT_Bone_Properties(bpy.types.Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'bone'
    bl_label = 'Dagor Bone Properties'

    @classmethod
    def poll(cls, context):
        return active_bone(context) is not None

    def draw(self, context):
        bone = active_bone(context)
        if 'dagor_script' in bone:
            self.layout.prop(bone, '["dagor_script"]', text='Script')
        row = self.layout.row(align=True)
        for operation, label in [('COPY', 'Copy'), ('PASTE', 'Paste'), ('CLEAR', 'Clear')]:
            row.operator('dt.bone_properties', text=label).operation = operation
        self.layout.operator('dt.bone_properties', text='Open as Text').operation = 'OPEN'
        self.layout.operator('dt.bone_properties', text='Apply from Text').operation = 'APPLY'


classes = (DAGOR_OT_Bone_Properties, DAGOR_PT_Bone_Properties)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
