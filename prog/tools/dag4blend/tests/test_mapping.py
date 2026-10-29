"""Blender regression checks for sparse and three-component DAG map channels."""
import io
from pathlib import Path

from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
namespace = {}
for filename in ('constants.py', 'face.py', 'node.py', 'mesh.py',
                 'exporter/writer.py', 'importer/reader.py', 'mapping.py'):
    source = (ROOT / filename).read_text()
    exec('\n'.join(line for line in source.splitlines() if not line.startswith('from .')), namespace)

for vertex_count in (3, 65536):
    mesh = namespace['MeshExp']()
    mesh.vertices = [Vector((index, 0, 0)) for index in range(vertex_count)]
    face = namespace['FaceExp']()
    face.f, face.smgr, face.mat = [0, 1, 2], 1, 0
    mesh.faces = [face]
    mesh.color_attributes = {(0.25, 0.5, 0.75, 1): 0}
    mesh.color_attributes_poly = [0, 0, 0]
    uv = Vector((0.5, 0.75)).freeze()
    mesh.uv = [{}, {}, {}, {}, {uv: 0}]
    mesh.uv_poly = [[], [], [], [], [0, 0, 0]]
    mesh.map_channels[8] = ([(0.2, 0.4, 0.6)], [0, 0, 0])
    writer = namespace['DagWriter']()
    writer.file = io.BytesIO()
    namespace['write_mesh_data'](writer, mesh)
    reader = namespace['DagReader']()
    reader.file, reader.eof = io.BytesIO(writer.file.getvalue()), False
    chunk = reader.beginChunk()
    big = vertex_count == 65536
    assert chunk.id == namespace['DAG_OBJ_BIGMESH' if big else 'DAG_OBJ_MESH']
    read_count = reader.readDWord if big else reader.readUShort
    assert read_count() == vertex_count
    for _ in range(vertex_count):
        reader.readVertex()
    face_count = read_count()
    assert face_count == 1
    (reader.readBigFace if big else reader.readFace)()
    parsed = namespace['MeshExp']()
    namespace['read_mesh_channels'](reader, parsed, face_count, big)
    assert len(parsed.uv) == 8
    assert parsed.uv[4] == [0.5, 0.75]
    assert parsed.color_attributes == [(0.25, 0.5, 0.75)]
    assert all(abs(a - b) < 1e-6 for a, b in zip(parsed.map_channels[8][0][0], (0.2, 0.4, 0.6)))
    assert reader.file.tell() == len(writer.file.getvalue())
print('PASS: sparse UV channel IDs, RGB component count, 3D AO maps, small/big mesh index widths')
