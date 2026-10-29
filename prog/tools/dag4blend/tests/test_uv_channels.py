"""Run with Blender --background --factory-startup --python this_file."""
import importlib.util
from pathlib import Path

import bpy

path = Path(__file__).resolve().parents[1] / 'tools/uv_tools.py'
spec = importlib.util.spec_from_file_location('dagor_uv_tools', path)
uv_tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uv_tools)
uv_tools.register()

mesh = bpy.data.meshes.new('UV test')
mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
mesh.uv_layers.new(name='UVMap')
original = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
other = [(0.5, 0.5)] * 3
uv_tools.write_uv(mesh.uv_layers[0], original)
uv_tools.transfer_uv(mesh, 1, 3, 'COPY')
assert len(mesh.uv_layers) == 3
assert uv_tools.read_uv(mesh.uv_layers[2]) == original
uv_tools.write_uv(mesh.uv_layers[2], other)
uv_tools.transfer_uv(mesh, 1, 3, 'SWAP')
assert uv_tools.read_uv(mesh.uv_layers[0]) == other
assert uv_tools.read_uv(mesh.uv_layers[2]) == original
uv_tools.transfer_uv(mesh, 3, 2, 'MOVE')
assert len(mesh.uv_layers) == 2
assert uv_tools.read_uv(mesh.uv_layers[1]) == original
uv_tools.transfer_uv(mesh, 1, 1, 'REMOVE')
assert len(mesh.uv_layers) == 1
assert uv_tools.read_uv(mesh.uv_layers[0]) == original
try:
    uv_tools.transfer_uv(mesh, 2, 1, 'COPY')
    raise AssertionError('Missing source must fail')
except ValueError:
    pass

# Multi-user meshes must be processed once, and a missing source on any
# selected mesh must cancel before modifying any of them.
bpy.ops.object.select_all(action='DESELECT')
objects = [bpy.data.objects.new(name, mesh) for name in ('shared A', 'shared B')]
for obj in objects:
    bpy.context.collection.objects.link(obj)
    obj.select_set(True)
bpy.context.view_layer.objects.active = objects[0]
assert bpy.ops.dt.uv_channel(operation='COPY', source=1, destination=2) == {'FINISHED'}
assert len(mesh.uv_layers) == 2
assert bpy.ops.dt.uv_channel(operation='REMOVE', source=1) == {'FINISHED'}
assert len(mesh.uv_layers) == 1, 'Shared data must only be modified once'
assert bpy.ops.dt.uv_buffer(operation='COPY', channel=1) == {'FINISHED'}
paste_mesh = mesh.copy()
paste_mesh.uv_layers.remove(paste_mesh.uv_layers[0])
paste_target = bpy.data.objects.new('paste target', paste_mesh)
bpy.context.collection.objects.link(paste_target)
bpy.ops.object.select_all(action='DESELECT')
paste_target.select_set(True)
bpy.context.view_layer.objects.active = paste_target
assert bpy.ops.dt.uv_buffer(operation='PASTE', channel=3) == {'FINISHED'}
assert uv_tools.read_uv(paste_mesh.uv_layers[2]) == original
bad_mesh = bpy.data.meshes.new('different indexed topology')
bad_mesh.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 2, 1)])
bad = bpy.data.objects.new('bad target', bad_mesh)
bpy.context.collection.objects.link(bad)
bpy.context.view_layer.update()
bad.select_set(True)
try:
    bpy.ops.dt.uv_buffer(operation='PASTE', channel=4)
    raise AssertionError('Mismatched topology was accepted')
except RuntimeError as error:
    assert 'topology' in str(error)
assert len(paste_mesh.uv_layers) == 3 and len(bad_mesh.uv_layers) == 0
uv_tools.unregister()
print('PASS: UV copy, swap, move, delete, missing channels, shared data, registration')
