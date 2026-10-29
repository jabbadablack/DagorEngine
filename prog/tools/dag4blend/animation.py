"""Sampled Anim-v2 (.a2d) export.

The source format is specified by maxplug/expUtil.cpp::save_anim2 and consumed
by sceneTools/assetExp/exporters/a2dExp.cpp. Keys use linear vector polynomials
and spherical quaternion interpolation between evaluated Blender samples.
"""
import math
import os
from pathlib import Path
import struct
import tempfile

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, StringProperty
from bpy_extras.io_utils import ExportHelper
from mathutils import Matrix, Vector
from .skin import native_pose_matrix


POINT3 = 0x577084E5
QUAT = 0x39056464
POSITION = 0xE66CF0CC
SCALE = 0x48D43D77
ROTATION = 0x8D490AE4
ORIGIN_LINEAR = 0x31DE5F48
ORIGIN_ANGULAR = 0x09FD7093
TICKS_PER_SECOND = 4800


def dag_decompose(matrix):
    """Match Max's interp_tm: put a reflected basis' negative scale on Z."""
    basis = matrix.to_3x3()
    scale = Vector(tuple(column.length for column in basis.col))
    if min(scale) <= 1e-12:
        raise ValueError('Animation transforms must not have a zero scale axis')
    if basis.determinant() < 0:
        scale.z = -scale.z
    for index in range(3):
        basis.col[index] = basis.col[index] / scale[index]
    return matrix.translation.copy(), basis.to_quaternion().normalized(), scale


def reduce_keys(times, values, tolerance, quaternion=False):
    """Keep endpoint samples and bound interpolation error at every input sample."""
    if len(times) <= 2 or tolerance <= 0:
        return times, values
    retained = {0, len(times) - 1}
    pending = [(0, len(times) - 1)]
    while pending:
        first, last = pending.pop()
        worst, split = tolerance, None
        for index in range(first + 1, last):
            fraction = (times[index] - times[first]) / (times[last] - times[first])
            if quaternion:
                predicted = values[first].normalized().slerp(values[last].normalized(), fraction)
                actual = values[index]
                dot = sum(a * b for a, b in zip(predicted, actual))
                norm = math.sqrt(sum(a * a for a in predicted) * sum(b * b for b in actual))
                error = 2 * math.acos(min(1, abs(dot) / norm))
            else:
                predicted = values[first].lerp(values[last], fraction)
                error = (predicted - values[index]).length
            if error > worst:
                worst, split = error, index
        if split is not None:
            retained.add(split)
            pending.extend(((first, split), (split, last)))
    indices = sorted(retained)
    return [times[index] for index in indices], [values[index] for index in indices]


def origin_velocities(matrices, times, looped=False):
    if len(matrices) != len(times) or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Origin matrices require matching, strictly increasing sample times')
    linear, angular = [], []
    converted = []
    for matrix in matrices:
        matrix = matrix.copy()
        matrix[1], matrix[2] = matrix[2].copy(), matrix[1].copy()
        converted.append(dag_decompose(matrix))
    for index in range(len(times)):
        if index + 1 == len(times):
            linear.append(linear[0].copy() if looped and linear else Vector())
            angular.append(Vector())
            break
        dt = times[index + 1] - times[index]
        position, rotation, _ = converted[index]
        next_position, next_rotation, _ = converted[index + 1]
        linear.append(rotation.inverted() @ (next_position - position) / dt)
        # Max samples row-vector quaternions, whose components are the
        # conjugates of Blender's column-vector quaternion representation.
        delta = (next_rotation.conjugated() @ rotation).normalized()
        if delta.w < 0:
            delta.negate()
        angular.append(delta.axis * delta.angle / dt if abs(delta.w) < 1 - 1e-7 else Vector())
    return linear, angular


def vector_keys(values):
    output = bytearray()
    for index, value in enumerate(values):
        following = values[min(index + 1, len(values) - 1)]
        delta = tuple(b - a for a, b in zip(value, following))
        output.extend(struct.pack('<12f', *value, *delta, 0, 0, 0, 0, 0, 0))
    return bytes(output)


def quaternion_keys(values):
    # Antipodal quaternion representations must not cause long-arc rotations.
    quats = []
    for value in values:
        quat = value.normalized()
        if quats and quats[-1].dot(quat) < 0:
            quat.negate()
        quats.append(quat)
    output = bytearray()
    for index, quat in enumerate(quats):
        following = quats[min(index + 1, len(quats) - 1)]
        angle = math.acos(max(-1.0, min(1.0, quat.dot(following))))
        # b0=p, b1=next: qsquad reduces to slerp for this segment.
        output.extend(struct.pack('<16f', angle, angle, math.sin(angle), math.sin(angle),
                                  quat.x, quat.y, quat.z, quat.w,
                                  quat.x, quat.y, quat.z, quat.w,
                                  following.x, following.y, following.z, following.w))
    return bytes(output)


def encode_a2d(tracks, times, labels=(), tolerances=None, velocities=None):
    """tracks maps node name to (position samples, quaternion samples, scale samples)."""
    if not tracks or not times:
        raise ValueError('Animation has no nodes or samples')
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Sample times must be strictly increasing at 4800 ticks per second')
    names = bytearray(b'\0')
    offsets = {}

    def name_offset(name):
        if not name or '\0' in name:
            raise ValueError('Animation names must be nonempty and contain no NUL characters')
        if name not in offsets:
            # Match the ASCII subset used by DAG node names, avoiding locale
            # dependent mismatches between animation and skeleton names.
            encoded = name.encode('ascii')
            offsets[name] = len(names)
            names.extend(encoded + b'\0')
        return offsets[name]

    for name, channels in tracks.items():
        name_offset(name)
        if len(channels) != 3 or any(len(channel) != len(times) for channel in channels):
            raise ValueError(f'{name}: channel sample counts do not match time pool')
    point_channels = []
    if velocities is not None:
        for kind, name, values in ((ORIGIN_LINEAR, 'origin_lin_vel_node_name', velocities[0]),
                                    (ORIGIN_ANGULAR, 'origin_ang_vel_node_name', velocities[1])):
            if len(values) != len(times):
                raise ValueError('Origin velocity sample counts do not match the timeline')
            name_offset(name)
            point_channels.append((kind, [(name, times, values)]))
    point_channels.extend((kind, [(name, times, values[component]) for name, values in tracks.items()])
                          for kind, component in ((POSITION, 0), (SCALE, 2)))
    rotation_channels = [(ROTATION, [(name, times, values[1]) for name, values in tracks.items()])]
    note_keys = [(name_offset(name), time) for name, time in labels]
    names.extend(b'\0' * (-len(names) % 8))
    time_pool = bytearray()
    key_pool = bytearray()
    type_records = bytearray()
    for data_type, channels in ((POINT3, point_channels), (QUAT, rotation_channels)):
        type_records.extend(struct.pack('<4I', data_type, len(key_pool), len(time_pool) // 4,
                                        len(channels)))
        for channel_type, node_channels in channels:
            if tolerances and channel_type in tolerances:
                node_channels = [(name, *reduce_keys(node_times, values, tolerances[channel_type], data_type == QUAT))
                                 for name, node_times, values in node_channels]
            count = len(node_channels)
            type_records.extend(struct.pack('<2I', channel_type, count))
            type_records.extend(struct.pack(f'<{count}I', *(len(values) for _, _, values in node_channels)))
            type_records.extend(struct.pack(f'<{count}I', *(offsets[name] for name, _, _ in node_channels)))
            type_records.extend(struct.pack(f'<{count}f', *([1.0] * count)))
            for _, node_times, values in node_channels:
                time_pool.extend(struct.pack(f'<{len(node_times)}i', *node_times))
                key_pool.extend(quaternion_keys(values) if data_type == QUAT else vector_keys(values))
    header = struct.pack('<4s8I', b'ANIM', 0x200, 36, 0, len(names), len(time_pool) // 4,
                         len(key_pool), len(note_keys), 2)
    notes = b''.join(struct.pack('<2i', offset, time) for offset, time in note_keys)
    return header + names + time_pool + key_pool + notes + type_records


def animation_targets(context, selected):
    objects = list(context.selected_objects if selected else context.scene.objects)
    for obj in list(objects):
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE' and modifier.show_viewport and modifier.object is not None:
                if modifier.object not in objects:
                    objects.append(modifier.object)
    # Include ancestors so transforms refer to the same hierarchy as the DAG.
    for obj in list(objects):
        parent = obj.parent
        while parent is not None:
            if parent not in objects:
                objects.append(parent)
            parent = parent.parent
    targets = []
    for obj in sorted(objects, key=lambda obj: obj.name):
        targets.append((obj.name, obj, None))
        if obj.type == 'ARMATURE':
            targets.extend((bone.name, obj, bone.name) for bone in obj.pose.bones)
    names = [name for name, _, _ in targets]
    if len(set(names)) != len(names):
        raise ValueError('Object and bone names must be unique across exported animation nodes')
    return targets


def sample_animation(context, start, end, samples_per_frame=1, selected=True, origin=None, origin_samples=None):
    if end < start:
        raise ValueError('End frame must be at or after start frame')
    if samples_per_frame < 1:
        raise ValueError('Samples per frame must be positive')
    targets = animation_targets(context, selected)
    if not targets:
        raise ValueError('No animation nodes selected')
    scene = context.scene
    fps = scene.render.fps / scene.render.fps_base
    sample_frames = [start + index / samples_per_frame
                     for index in range((end - start) * samples_per_frame + 1)]
    times = [round((frame - start) * TICKS_PER_SECOND / fps) for frame in sample_frames]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Sampling rate exceeds the 4800-tick animation time resolution')
    tracks = {name: ([], [], []) for name, _, _ in targets}
    saved_frame, saved_subframe = scene.frame_current, scene.frame_subframe
    depsgraph = context.evaluated_depsgraph_get()
    try:
        for frame in sample_frames:
            scene.frame_set(math.floor(frame), subframe=frame - math.floor(frame))
            origin_world = origin.evaluated_get(depsgraph).matrix_world.copy() if origin is not None else None
            if origin_samples is not None and origin_world is not None:
                origin_samples.append(origin_world)
            for name, obj, bone_name in targets:
                evaluated = obj.evaluated_get(depsgraph)
                if bone_name is not None:
                    bone = evaluated.pose.bones[bone_name]
                    tm = native_pose_matrix(bone)
                    if bone.parent is not None:
                        tm = native_pose_matrix(bone.parent).inverted_safe() @ tm
                else:
                    tm = evaluated.matrix_world.copy()
                    if obj.parent is not None:
                        parent = obj.parent.evaluated_get(depsgraph)
                        parent_tm = parent.matrix_world.copy()
                        if obj.parent_type == 'BONE':
                            parent_tm = parent_tm @ native_pose_matrix(parent.pose.bones[obj.parent_bone])
                        tm = parent_tm.inverted_safe() @ tm
                    else:
                        if origin_world is not None:
                            tm = origin_world.inverted_safe() @ tm
                        tm[1], tm[2] = tm[2].copy(), tm[1].copy()
                position, rotation, scale = dag_decompose(tm)
                reconstructed = Matrix.LocRotScale(position, rotation, scale)
                if any(abs(tm[i][j] - reconstructed[i][j]) > 1e-4
                       for i in range(4) for j in range(4)):
                    raise ValueError(f'{name} at frame {frame}: shear cannot be represented by animation TRS keys')
                for channel, value in zip(tracks[name], (position, rotation, scale)):
                    channel.append(value.copy())
    finally:
        scene.frame_set(saved_frame, subframe=saved_subframe)
    labels = [(marker.name, round((marker.frame - start) * TICKS_PER_SECOND / fps))
              for marker in sorted(scene.timeline_markers, key=lambda marker: marker.frame)
              if start <= marker.frame <= end]
    return tracks, times, labels


class DAGOR_OT_Export_Animation(bpy.types.Operator, ExportHelper):
    bl_idname = 'export_scene.dagor_a2d'
    bl_label = 'Export Dagor Animation'
    filename_ext = '.a2d'
    filter_glob: StringProperty(default='*.a2d', options={'HIDDEN'})
    selected: BoolProperty(name='Selected objects', default=True)
    start: IntProperty(name='Start frame', default=1)
    end: IntProperty(name='End frame', default=250)
    samples_per_frame: IntProperty(name='Samples per frame', default=1, min=1, max=8)
    optimize: BoolProperty(name='Reduce redundant keys', default=True)
    position_tolerance: FloatProperty(name='Position tolerance', default=0.0001, min=0)
    rotation_tolerance: FloatProperty(name='Rotation tolerance', default=0.0001, min=0, subtype='ANGLE')
    scale_tolerance: FloatProperty(name='Scale tolerance', default=0.0001, min=0)
    origin_name: StringProperty(name='Motion origin object')
    looped: BoolProperty(name='Loop origin velocity', default=False)

    def invoke(self, context, event):
        self.start, self.end = context.scene.frame_start, context.scene.frame_end
        return ExportHelper.invoke(self, context, event)

    def execute(self, context):
        temporary = None
        try:
            origin = bpy.data.objects.get(self.origin_name) if self.origin_name else None
            if self.origin_name and (origin is None or origin.name not in context.scene.objects):
                raise ValueError('Motion origin must be an object in the current scene')
            origin_samples = []
            tracks, times, labels = sample_animation(context, self.start, self.end,
                                                    self.samples_per_frame, self.selected, origin, origin_samples)
            tolerances = {POSITION: self.position_tolerance, ROTATION: self.rotation_tolerance,
                          SCALE: self.scale_tolerance} if self.optimize else None
            velocities = origin_velocities(origin_samples, times, self.looped) if origin is not None else None
            payload = encode_a2d(tracks, times, labels, tolerances, velocities)
            destination = Path(self.filepath)
            with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.a2d.tmp', delete=False) as output:
                temporary = output.name
                output.write(payload)
            os.replace(temporary, destination)
            temporary = None
        except (ValueError, OSError, OverflowError, struct.error) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        finally:
            if temporary is not None:
                os.unlink(temporary)
        self.report({'INFO'}, f'Exported {len(tracks)} nodes, {len(times)} samples and {len(labels)} labels')
        return {'FINISHED'}


def menu_export(self, context):
    self.layout.operator(DAGOR_OT_Export_Animation.bl_idname, text='Dagor Animation (.a2d)')


def register():
    bpy.utils.register_class(DAGOR_OT_Export_Animation)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)
    bpy.utils.unregister_class(DAGOR_OT_Export_Animation)
