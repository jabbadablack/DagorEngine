"""Run with Blender --background --factory-startup --python-exit-code 1 --python this_file."""
import importlib.util
from pathlib import Path

import bpy
from mathutils import Vector

path = Path(__file__).resolve().parents[1] / 'tools/authoring.py'
spec = importlib.util.spec_from_file_location('dagor_authoring_test', path)
authoring = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authoring)
authoring.register()
assert authoring.clean_asset_name('Дерево Тест') == 'Derevo_Test'
assert authoring.clean_asset_name('Hello World', replacement='', lowercase=True) == 'helloworld'
assert authoring.clean_asset_name('CON') == '_CON'

bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16)
source = bpy.context.object
source.name = 'asset'
source.location = (4, 5, 6)
bpy.context.view_layer.update()
original_coordinates = [tuple(vert.co) for vert in source.data.vertices]
original_faces = len(source.data.polygons)
original_uvs = [tuple(loop.uv) for loop in source.data.uv_layers[0].data]
lods = authoring.generate_lods(bpy.context, source, 2, 0.5)
source.data.calc_loop_triangles()
previous_triangles = len(source.data.loop_triangles)
for index, lod in enumerate(lods, 1):
    lod.data.calc_loop_triangles()
    triangles = len(lod.data.loop_triangles)
    assert 0 < triangles < previous_triangles
    previous_triangles = triangles
    assert lod.name == f'asset.lod{index:02d}'
    assert lod.data.uv_layers
    assert lod.matrix_world == source.matrix_world
assert len(source.data.polygons) == original_faces
assert [tuple(vert.co) for vert in source.data.vertices] == original_coordinates
assert [tuple(loop.uv) for loop in source.data.uv_layers[0].data] == original_uvs
collision = authoring.generate_collision(bpy.context, source)
assert collision.data.polygons and collision.matrix_world == source.matrix_world
assert not collision.data.materials
bpy.ops.mesh.primitive_cube_add()
cut_source = bpy.context.object
cut_collision = authoring.generate_collision(bpy.context, cut_source, cut_height=0)
assert max(vertex.co.z for vertex in cut_collision.data.vertices) <= 1e-6
assert min(vertex.co.z for vertex in cut_collision.data.vertices) < -0.9

# A plane's known world-space normals provide a deterministic transfer oracle.
bpy.ops.mesh.primitive_plane_add()
plane = bpy.context.object
plane.location = (0, 0, 0.2)
bpy.ops.mesh.primitive_plane_add()
target = bpy.context.object
bpy.context.view_layer.update()
authoring.transfer_normals(bpy.context, plane, target)
assert target.data.has_custom_normals
for normal in target.data.corner_normals:
    assert normal.vector.dot(Vector((0, 0, 1))) > 0.999
authoring.puff_normals(target, center_height=-1)
assert target.data.has_custom_normals
for normal in target.data.corner_normals:
    assert normal.vector.z > 0
material = bpy.data.materials.new('tree_bark')
target.data.materials.append(material)
before = [normal.vector.copy() for normal in target.data.corner_normals]
authoring.puff_normals(target, center_height=10, keep_material='bark')
assert all((normal.vector - expected).length < 1e-4
           for normal, expected in zip(target.data.corner_normals, before))

objects_before = set(bpy.data.objects)
meshes_before = set(bpy.data.meshes)
authoring.volume_normals(bpy.context, source, 0.4, 1, '')
assert source.data.has_custom_normals
assert set(bpy.data.objects) == objects_before
assert set(bpy.data.meshes) == meshes_before, 'Temporary volume meshes leaked'
volume = authoring.volume_normals(bpy.context, source, 0.4, 1, '',
                                  keep_volume=True, surface_size=0.2, tension=0.5)
assert volume.hide_get()
volume_mesh = volume.data
bpy.data.objects.remove(volume, do_unlink=True)
bpy.data.meshes.remove(volume_mesh)
authoring.unregister()
print('PASS: LOD triangle reduction, source UV/geometry preservation, convex collision, normal transfer, puffiness, volume cleanup')
