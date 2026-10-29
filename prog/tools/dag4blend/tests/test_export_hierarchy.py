"""Run with Blender: blender --background --factory-startup --python this_file.

Load the exporter methods independently so these format tests don't need add-on
preferences, shader assets, or an installed copy of dag4blend.
"""
import ast
import io
import struct
from pathlib import Path

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[1]
namespace = {'bpy': bpy, 'Matrix': Matrix, 'log': lambda *a, **k: None,
             'is_matrix_ok': lambda matrix: True,
             'SUPPORTED_TYPES': ('MESH', 'CURVE', 'EMPTY')}
exec((ROOT / 'constants.py').read_text(), namespace)
exec((ROOT / 'node.py').read_text(), namespace)
writer_source = (ROOT / 'exporter/writer.py').read_text()
writer_source = '\n'.join(line for line in writer_source.splitlines()
                          if not line.startswith('from ..'))
exec(writer_source, namespace)
tree = ast.parse((ROOT / 'exporter/exporter.py').read_text())
exporter = next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == 'DagExporter')
methods = {'enumerate', 'saveNode', 'saveHelper', 'saveChildren', 'saveNodes'}
exporter.bases = []
exporter.body = [node for node in exporter.body
                 if isinstance(node, ast.FunctionDef) and node.name in methods]
exec(compile(ast.fix_missing_locations(ast.Module(body=[exporter], type_ignores=[])),
             '<exporter methods>', 'exec'), namespace)
Exporter = namespace['DagExporter']


def assert_matrix(actual, expected):
    assert all(abs(actual[i][j] - expected[i][j]) < 1e-5
               for i in range(4) for j in range(4)), (actual, expected)


def chunks(data):
    offset = 0
    while offset < len(data):
        size, tag = struct.unpack_from('<II', data, offset)
        yield tag, data[offset + 8:offset + 4 + size]
        offset += size + 4
    assert offset == len(data)


def test_helpers_and_transforms():
    parent = bpy.data.objects.new('group', None)
    child = bpy.data.objects.new('child', None)
    sibling = bpy.data.objects.new('sibling', None)
    for obj in (parent, child, sibling):
        bpy.context.scene.collection.objects.link(obj)
    parent.matrix_world = (Matrix.Translation((10, 20, 30))
                           @ Matrix.Rotation(0.7, 4, 'Z')
                           @ Matrix.Diagonal((2, 3, 4, 1)))
    child.parent = parent
    child.matrix_parent_inverse = Matrix.Translation((-3, 2, 1))
    child.matrix_basis = Matrix.Translation((4, 5, 6))
    bpy.context.view_layer.update()
    exp = Exporter()
    exp.nodes, exp.last_index = [], 0
    exp.gatherObjPropScript = lambda obj, node: 'group:b=yes'
    root = namespace['NodeExp']()
    root.id, root.parent_id = 65535, -1
    assert exp.enumerate([parent, child, sibling], [parent, sibling], root,
                         bpy.context.scene, parent.matrix_world.inverted()) == 0
    assert len(root.children) == 2, 'Helper must not stop traversal of siblings'
    group = root.children[0]
    assert len(group.children) == 1
    # Top-level nodes swap Y/Z before transposition; identity becomes a swap.
    expected = Matrix.Identity(4)
    expected[1], expected[2] = expected[2].copy(), expected[1].copy()
    assert_matrix(group.tm, expected.transposed())
    assert_matrix(group.children[0].tm,
                  (parent.matrix_world.inverted() @ child.matrix_world).transposed())
    exp.writer = namespace['DagWriter']()
    exp.writer.file = io.BytesIO()
    exp.saveNodes(root)
    root_tag, root_data = next(chunks(exp.writer.file.getvalue()))
    assert root_tag == namespace['DAG_NODE']
    children = dict(chunks(root_data))[namespace['DAG_NODE_CHILDREN']]
    serialized = list(chunks(children))
    assert len(serialized) == 2
    group_chunks = dict(chunks(serialized[0][1]))
    assert group_chunks[namespace['DAG_NODE_SCRIPT']] == b'group:b=yes'
    assert namespace['DAG_NODE_TM'] in group_chunks
    assert namespace['DAG_NODE_OBJ'] not in group_chunks
    assert len(list(chunks(group_chunks[namespace['DAG_NODE_CHILDREN']]))) == 1
    failed_mesh = bpy.data.objects.new('failed mesh', bpy.data.meshes.new('failed'))
    bpy.context.scene.collection.objects.link(failed_mesh)
    failed_mesh.parent = parent
    exp.dumpMesh = lambda *args: None
    root.children.clear()
    assert exp.enumerate([parent, failed_mesh], [parent], root,
                         bpy.context.scene) == -1, 'Nested mesh failures must propagate'
    print('PASS: helper hierarchy, sibling traversal, parent inverse, local pivot, DAG chunks')


test_helpers_and_transforms()
