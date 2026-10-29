"""Small DAG graybox meshes, using the public DagSaver binary format."""
import math
from pathlib import Path
import struct


def block(tag, payload=b''):
    return struct.pack('<II', len(payload) + 4, tag) + payload


def dag(name, vertices, triangles):
    material_name, shader = b'graybox', b'rendinst_simple'
    # DagMater: BGRA-free BGR colors, power, flags, 16 texture IDs, 8 reserved IDs.
    material = bytes((100, 100, 100, 180, 180, 180, 0, 0, 0, 0, 0, 0))
    material += struct.pack('<fI', 0.0, 0x80000000) + struct.pack('<16H8H', *([65535] * 16), *([0] * 8))
    material = bytes([len(material_name)]) + material_name + material + bytes([len(shader)]) + shader
    mesh = struct.pack('<H', len(vertices)) + b''.join(struct.pack('<3f', *v) for v in vertices)
    mesh += struct.pack('<H', len(triangles)) + b''.join(struct.pack('<3HIH', *t, 1, 0) for t in triangles)
    mesh += b'\x00'  # no UV channels; the graybox material uses solid color
    transform = struct.pack('<12f', 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
    node = block(1, transform) + block(2, struct.pack('<HHI', 1, 0, 7) + name.encode())
    node += block(5, struct.pack('<H', 0)) + block(4, block(1, mesh))
    root_node = block(2, struct.pack('<HHI', 0, 1, 0)) + block(7, block(1, node))
    return struct.pack('<I', 0x1A474144) + block(0x1A474144, block(2, material) + block(1, root_node) + block(0))


def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    cube = [(-.5,-.5,-.5), (.5,-.5,-.5), (.5,.5,-.5), (-.5,.5,-.5),
            (-.5,-.5,.5), (.5,-.5,.5), (.5,.5,.5), (-.5,.5,.5)]
    faces = [(0,2,1), (0,3,2), (4,5,6), (4,6,7), (0,1,5), (0,5,4),
             (3,6,2), (3,7,6), (0,4,7), (0,7,3), (1,2,6), (1,6,5)]
    meshes = {'cube': (cube, faces), 'plane': ([(-5,0,-5), (-5,0,5), (5,0,5), (5,0,-5)], [(0,1,2),(0,2,3)])}
    vertices = [(0, 1, 0)]
    rings, segments = 7, 16
    for ring in range(1, rings + 1):
        phi = math.pi * ring / (rings + 1)
        for segment in range(segments):
            theta = math.tau * segment / segments
            vertices.append((math.sin(phi)*math.cos(theta), math.cos(phi), math.sin(phi)*math.sin(theta)))
    vertices.append((0,-1,0))
    triangles = []
    for j in range(segments):
        triangles.append((0, 1+(j+1)%segments, 1+j))
        for ring in range(rings-1):
            a, b = 1+ring*segments+j, 1+ring*segments+(j+1)%segments
            triangles += [(a,b,b+segments), (a,b+segments,a+segments)]
        a, b = 1+(rings-1)*segments+j, 1+(rings-1)*segments+(j+1)%segments
        triangles.append((a,b,len(vertices)-1))
    meshes['sphere'] = vertices, triangles
    for name, (vertices, triangles) in meshes.items():
        (directory / f'{name}.lod00.dag').write_bytes(dag(name, vertices, triangles))
    (directory / '.folder.blk').write_text('''export { gameResPack:t="primitives.grp" }
virtual_res_blk {
  find:t="^(.*)\\.lod00\\.dag$"
  className:t="rendInst"
  name:t="$1"
  contents { lod { range:r=10000; } }
}
''')
