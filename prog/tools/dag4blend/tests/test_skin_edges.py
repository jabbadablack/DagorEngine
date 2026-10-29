"""Native-style mesh bones, unweighted ancestors and affine bind preservation."""
import importlib
from pathlib import Path
import sys
import types

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
package = types.ModuleType('dagor_skin_fixture')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
skin = importlib.import_module(package.__name__ + '.skin')
Node = importlib.import_module(package.__name__ + '.node').NodeExp

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
collection = bpy.data.collections.new('native_skin')
bpy.context.scene.collection.children.link(collection)


def node_object(name, node_id, parent=None, mesh=False):
    data = None
    if mesh:
        data = bpy.data.meshes.new(name)
        data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [], [(0, 1, 2)])
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    obj.parent = parent
    obj['_dag_node_id'] = node_id
    node = Node()
    node.id, node.name = node_id, name
    return node, obj


group_node, group = node_object('original_group', 10)
group.matrix_world = Matrix.Translation((3, 4, 5))
root_node, root = node_object('unweighted_root', 11, group)
root.matrix_world = group.matrix_world @ Matrix.Translation((1, 0, 0))
bone_node, bone_geometry = node_object('mesh_bone', 12, root, True)
raw_bind = Matrix.Translation((1, 0, 0)) @ Matrix.Diagonal((2, 1, 0.5, 1))
bone_geometry.matrix_world = group.matrix_world @ raw_bind
bone_node.objProps = 'label:t="Native Bone Script"'
body_node, body = node_object('skin_body', 13, mesh=True)
stored = bone_geometry.matrix_world.copy()
stored[1], stored[2] = stored[2].copy(), stored[1].copy()
body_node.skin = ([(12, stored.transposed())], [[1, 1, 1]])
group_node.children = [root_node]
root_node.children = [bone_node]
scene_root = Node()
scene_root.id = 65535
scene_root.children = [group_node, body_node]
bpy.context.view_layer.update()
before_geometry = bone_geometry.matrix_world.copy()
skin.restore_skins(bpy.context, collection, scene_root)
bpy.context.view_layer.update()
rig = next(obj for obj in collection.objects if obj.type == 'ARMATURE')
assert rig.name == 'original_group'
assert set(rig.data.bones.keys()) == {'unweighted_root', 'mesh_bone'}
assert rig.data.bones['mesh_bone'].parent == rig.data.bones['unweighted_root']
assert rig.data.bones['mesh_bone']['dagor_script'] == bone_node.objProps
retained = bpy.data.objects['mesh_bone_geometry']
assert retained.parent == rig and retained.parent_bone == 'mesh_bone'
assert max(abs(retained.matrix_world[i][j] - before_geometry[i][j])
           for i in range(4) for j in range(4)) < 1e-5
actual_bind = skin.effective_bind(rig.data.bones['mesh_bone'])
assert max(abs(actual_bind[i][j] - raw_bind[i][j]) for i in range(4) for j in range(4)) < 1e-5
rig.pose.bones['mesh_bone'].location = (1, 0, 0)
bpy.context.view_layer.update()
native_pose = skin.native_pose_matrix(rig.pose.bones['mesh_bone'])
expected_pose = Matrix.Translation((1, 0, 0)) @ raw_bind
assert max(abs(native_pose[i][j] - expected_pose[i][j]) for i in range(4) for j in range(4)) < 1e-5
evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
for vertex, original in zip(evaluated.data.vertices, body.data.vertices):
    assert (body.matrix_world @ vertex.co - (original.co + Vector((1, 0, 0)))).length < 1e-5
assert abs(retained.matrix_world.translation.x - before_geometry.translation.x - 1) < 1e-5
print('PASS: mesh-bone geometry retained, unweighted ancestors, scripts, affine binds, pose adapter and evaluated deformation')
