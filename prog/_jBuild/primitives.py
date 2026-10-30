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
    material += struct.pack('<fI', 0.0, 0x80000000) + struct.pack('<16H8H', 0, *([65535] * 15), *([0] * 8))
    material = bytes([len(material_name)]) + material_name + material + bytes([len(shader)]) + shader
    mesh = struct.pack('<H', len(vertices)) + b''.join(struct.pack('<3f', *v) for v in vertices)
    mesh += struct.pack('<H', len(triangles)) + b''.join(struct.pack('<3HIH', *t, 1, 0) for t in triangles)
    mesh += b'\x01' + struct.pack('<HBB', len(vertices), 2, 1)
    mesh += b''.join(struct.pack('<2f', x, z) for x, y, z in vertices)
    mesh += b''.join(struct.pack('<3H', *t) for t in triangles)
    transform = struct.pack('<12f', 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0)
    node = block(1, transform) + block(2, struct.pack('<HHI', 1, 0, 7) + name.encode())
    node += block(5, struct.pack('<H', 0)) + block(4, block(1, mesh))
    root_node = block(2, struct.pack('<HHI', 0, 1, 0)) + block(7, block(1, node))
    texture = b'starter_white.tga'
    textures = block(3, struct.pack('<HB', 1, len(texture)) + texture)
    return struct.pack('<I', 0x1A474144) + block(0x1A474144, textures + block(2, material) + block(1, root_node) + block(0))


def generate(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    # An original solid-white image supplies the diffuse slot required by the
    # stock rendinst shader. Material colors provide the graybox appearance.
    header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, 4, 4, 24, 32)
    (directory / 'starter_white.tga').write_bytes(header + bytes([255] * (4 * 4 * 3)))
    def sprite(name, size, pixel):
        header = struct.pack('<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, size, size, 32, 40)
        pixels = bytearray()
        for y in range(size):
            for x in range(size):
                value, alpha = pixel((x + .5) / size * 2 - 1, (y + .5) / size * 2 - 1)
                c = round(max(0, min(1, value)) * 255)
                pixels.extend((c, c, c, round(max(0, min(1, alpha)) * 255)))
        (directory / (name + '.tga')).write_bytes(header + pixels)
    # Original procedural sprites for the sky library's required texture slots.
    sprite('stars', 32, lambda x, y: (math.exp(-24 * (x*x + y*y)), 1))
    sprite('moon', 64, lambda x, y: (.65 + .12*math.sin(19*x)*math.cos(23*y), float(x*x + y*y < 1)))
    sprite('strata_clouds_simple', 64, lambda x, y: (.5 + .2*math.sin(7*x + 3*y)*math.cos(11*y - x), 1))
    sprite('assets_color_global_tex_palette', 64, lambda x, y: (.6 + .4*(x + 1)/2, 1))
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
virtual_res_blk {
  find:t="^(starter_white|stars|moon|strata_clouds_simple|assets_color_global_tex_palette)\\.tga$"
  className:t="tex"
  name:t="$1"
  contents { convert:b=yes; fmt:t="DXT5"; gamma:r=2.2; addrU:t="wrap"; addrV:t="wrap"; }
}
''')
