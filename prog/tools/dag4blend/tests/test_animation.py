"""Blender --background --factory-startup --python-exit-code 1 --python this_file."""
import importlib.util
import math
from pathlib import Path
import struct
import sys
import types

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType('dagor_animation_fixture')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location(package.__name__ + '.animation', ROOT / 'animation.py')
animation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(animation)
animation.register()


def read_source_a2d(payload):
    # Independent reader matching a2dExp.cpp's v0x200 loading order.
    magic, version, size, reserved, name_size, time_count, key_size, labels, type_count = struct.unpack_from('<4s8I', payload)
    assert (magic, version, size, reserved, type_count) == (b'ANIM', 0x200, 36, 0, 2)
    assert name_size % 8 == 0
    names = payload[36:36 + name_size]
    offset = 36 + name_size
    times = struct.unpack_from(f'<{time_count}i', payload, offset)
    offset += 4 * time_count
    keys = payload[offset:offset + key_size]
    offset += key_size
    notes = []

    def get_name(index):
        return names[index:names.index(b'\0', index)].decode('ascii')

    for _ in range(labels):
        name, tick = struct.unpack_from('<2i', payload, offset)
        offset += 8
        notes.append((get_name(name), tick))
    result = {}
    for _ in range(type_count):
        data_type, key_offset, time_offset, channels = struct.unpack_from('<4I', payload, offset)
        offset += 16
        for _ in range(channels):
            channel_type, node_count = struct.unpack_from('<2I', payload, offset)
            offset += 8
            counts = struct.unpack_from(f'<{node_count}I', payload, offset)
            offset += node_count * 4
            ids = struct.unpack_from(f'<{node_count}I', payload, offset)
            offset += node_count * 4
            weights = struct.unpack_from(f'<{node_count}f', payload, offset)
            offset += node_count * 4
            assert all(weight == 1 for weight in weights)
            key_floats = 12 if data_type == animation.POINT3 else 16
            for count, name_id in zip(counts, ids):
                channel_times = times[time_offset:time_offset + count]
                values = [struct.unpack_from(f'<{key_floats}f', keys, key_offset + index * key_floats * 4)
                          for index in range(count)]
                result[get_name(name_id), channel_type] = (channel_times, values)
                key_offset += count * key_floats * 4
                time_offset += count
    assert offset == len(payload), (offset, len(payload))
    return result, notes


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.fps, scene.render.fps_base = 24, 1
parent = bpy.data.objects.new('root', None)
child = bpy.data.objects.new('moving', None)
for obj in (parent, child):
    scene.collection.objects.link(obj)
    obj.select_set(True)
child.parent = parent
parent.location = (10, 20, 30)
child.rotation_mode = 'QUATERNION'
for frame, location, angle in ((0, (1, 2, 3), 0), (2, (5, 6, 7), math.pi / 2)):
    child.location = location
    child.rotation_quaternion = Quaternion((0, 0, 1), angle)
    child.keyframe_insert('location', frame=frame)
    child.keyframe_insert('rotation_quaternion', frame=frame)
scene.timeline_markers.new('start', frame=0)
scene.timeline_markers.new('end', frame=2)
scene.frame_set(1, subframe=0.25)
tracks, times, labels = animation.sample_animation(bpy.context, 0, 2, 2)
assert scene.frame_current == 1 and scene.frame_subframe == 0.25
assert times == [0, 100, 200, 300, 400]
payload = animation.encode_a2d(tracks, times, labels)
decoded, notes = read_source_a2d(payload)
assert notes == [('start', 0), ('end', 400)]
assert len(decoded) == 6
for name, (positions, rotations, scales) in tracks.items():
    for channel_type, values in ((animation.POSITION, positions), (animation.SCALE, scales)):
        channel_times, keys = decoded[name, channel_type]
        assert list(channel_times) == times
        for index, key in enumerate(keys):
            assert (Vector(key[:3]) - values[index]).length < 1e-5
            # Evaluate the cubic polynomial at the end of each segment.
            endpoint = sum((Vector(key[i:i + 3]) for i in range(0, 12, 3)), Vector())
            assert (endpoint - values[min(index + 1, len(values) - 1)]).length < 1e-5
    _, keys = decoded[name, animation.ROTATION]
    for index, key in enumerate(keys):
        quat = Quaternion((key[7], *key[4:7]))
        following = Quaternion((keys[min(index + 1, len(keys) - 1)][7],
                                *keys[min(index + 1, len(keys) - 1)][4:7]))
        assert abs(quat.dot(rotations[index])) > 1 - 1e-5
        assert quat.dot(following) >= 0
        assert abs(key[0] - math.acos(min(1.0, max(-1.0, quat.dot(following))))) < 1e-3

# Restored root TRS must match the DAG root coordinate conversion exactly.
tm = Matrix.LocRotScale(*(tracks['root'][index][0] for index in range(3)))
expected = parent.matrix_world.copy()
expected[1], expected[2] = expected[2].copy(), expected[1].copy()
assert max(abs(tm[i][j] - expected[i][j]) for i in range(4) for j in range(4)) < 1e-5
assert tuple(tracks['root'][2][0]) == (1, 1, -1), 'Signed scale must match Max interp_tm'

linear_times, linear_values = animation.reduce_keys([0, 100, 200],
    [Vector((0, 0, 0)), Vector((1, 2, 3)), Vector((2, 4, 6))], 1e-5)
assert linear_times == [0, 200]
peak_times, _ = animation.reduce_keys([0, 100, 200],
    [Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 0, 0))], 0.01)
assert peak_times == [0, 100, 200]
optimized, _ = read_source_a2d(animation.encode_a2d(tracks, times, labels,
    {animation.POSITION: 1e-4, animation.SCALE: 1e-4, animation.ROTATION: 1e-4}))
assert len(optimized['root', animation.POSITION][0]) == 2
assert len(optimized['root', animation.ROTATION][0]) == 2
origin_matrices = [Matrix.Translation((index, 0, 0)) for index in range(3)]
velocities = animation.origin_velocities(origin_matrices, [0, 200, 400])
assert (velocities[0][0] - Vector((0.005, 0, 0))).length < 1e-6
assert velocities[0][-1].length == 0 and all(value.length == 0 for value in velocities[1])
assert animation.origin_velocities(origin_matrices, [0, 200, 400], True)[0][-1] == velocities[0][0]
origins = []
relative, relative_times, relative_labels = animation.sample_animation(
    bpy.context, 0, 2, origin=parent, origin_samples=origins)
assert all(value.length < 1e-5 for value in relative['root'][0])
with_velocities, _ = read_source_a2d(animation.encode_a2d(relative, relative_times,
    relative_labels, velocities=animation.origin_velocities(origins, relative_times)))
assert ('origin_lin_vel_node_name', animation.ORIGIN_LINEAR) in with_velocities
assert ('origin_ang_vel_node_name', animation.ORIGIN_ANGULAR) in with_velocities

# Actual evaluated pose-bone samples, including parent-relative bind transforms.
bpy.ops.object.select_all(action='DESELECT')
bpy.ops.object.armature_add()
armature = bpy.context.object
armature.name = 'rig'
bone = armature.pose.bones[0]
bone.name = 'joint'
bone.location = (0, 0, 0)
bone.keyframe_insert('location', frame=0)
bone.location = (0, 0, 2)
bone.keyframe_insert('location', frame=2)
rig_tracks, rig_times, _ = animation.sample_animation(bpy.context, 0, 2)
assert set(rig_tracks) == {'rig', 'joint'}
assert (rig_tracks['joint'][0][-1] - rig_tracks['joint'][0][0]).length > 1.9
read_source_a2d(animation.encode_a2d(rig_tracks, rig_times))
assert scene.frame_current == 1 and scene.frame_subframe == 0.25
animation.unregister()
print('PASS: A2D v0x200 pools/channels, vector interpolation, quaternion tracks, FPS, labels, evaluated armature, frame restoration')
