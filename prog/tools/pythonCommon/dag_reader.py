# Minimal reader for the node hierarchy of .dag files (prog/tools/sharedInclude/libTools/dagFileRW/dagFileFormat.h).
# Reads node names, scripts, local tms, mesh vertices and skin (DAG_OBJ_BONES) data; enough to validate exported assets.
import struct

DAG_ID = 0x1A474144
DAG_NODE = 1

DAG_NODE_TM = 1
DAG_NODE_DATA = 2
DAG_NODE_SCRIPT = 3
DAG_NODE_OBJ = 4
DAG_NODE_CHILDREN = 7

DAG_OBJ_MESH = 1
DAG_OBJ_BIGMESH = 2
DAG_OBJ_BONES = 4

IDENT_TM = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0)]


class DagNode:
  def __init__(self):
    self.id = 0xFFFF
    self.name = ''
    self.flags = 0
    self.script = ''
    self.tm = None          # 4 rows of 3 floats: x axis, y axis, z axis, translation (parent space)
    self.children = []
    self.parent = None
    self.vertices = None    # mesh nodes only, node-local positions
    self.bones = None       # [(node id, bind tm rows)], skinned meshes only
    self.weights = None     # bone-major list, weights[b * len(vertices) + v]

  def walk(self):
    yield self
    for c in self.children:
      yield from c.walk()


def _chunks(data, ofs, end):
  while ofs < end:
    size, tag = struct.unpack_from('<II', data, ofs)
    yield tag, ofs + 8, ofs + 4 + size
    ofs += 4 + size


def _read_obj(node, data, ofs, end):
  for tag, b, e in _chunks(data, ofs, end):
    if tag in (DAG_OBJ_MESH, DAG_OBJ_BIGMESH):
      fmt, size = ('<H', 2) if tag == DAG_OBJ_MESH else ('<I', 4)
      count = struct.unpack_from(fmt, data, b)[0]
      v = struct.unpack_from(f'<{count * 3}f', data, b + size)
      node.vertices = [v[i:i + 3] for i in range(0, len(v), 3)]
    elif tag == DAG_OBJ_BONES:
      count = struct.unpack_from('<H', data, b)[0]
      p = b + 2
      node.bones = []
      for _ in range(count):
        values = struct.unpack_from('<H12f', data, p)
        node.bones.append((values[0], [values[1:4], values[4:7], values[7:10], values[10:13]]))
        p += 2 + 48
      vertex_count = struct.unpack_from('<I', data, p)[0]
      node.weights = list(struct.unpack_from(f'<{count * vertex_count}f', data, p + 4))


def _read_node(data, ofs, end, parent):
  node = DagNode()
  node.parent = parent
  for tag, b, e in _chunks(data, ofs, end):
    if tag == DAG_NODE_DATA:
      node.id, _, node.flags = struct.unpack_from('<HHI', data, b)
      node.name = data[b + 8:e].decode('ascii', errors='replace')
    elif tag == DAG_NODE_SCRIPT:
      node.script = data[b:e].decode('ascii', errors='replace')
    elif tag == DAG_NODE_TM:
      v = struct.unpack_from('<12f', data, b)
      node.tm = [v[0:3], v[3:6], v[6:9], v[9:12]]
    elif tag == DAG_NODE_OBJ:
      _read_obj(node, data, b, e)
    elif tag == DAG_NODE_CHILDREN:
      for ctag, cb, ce in _chunks(data, b, e):
        if ctag == DAG_NODE:
          node.children.append(_read_node(data, cb, ce, node))
  return node


def read_dag(path):
  """Returns the root DagNode (id 0xFFFF) of the file's node hierarchy."""
  with open(path, 'rb') as f:
    data = f.read()
  if struct.unpack_from('<I', data, 0)[0] != DAG_ID:
    raise ValueError(f'{path}: not a dag file')
  for tag, b, e in _chunks(data, 4, len(data)):
    if tag != DAG_ID:
      continue
    for ntag, nb, ne in _chunks(data, b, e):
      if ntag == DAG_NODE:
        return _read_node(data, nb, ne, None)
  raise ValueError(f'{path}: no node hierarchy')


def node_wtm(node):
  """World tm of a node as 4 rows (rows-as-axes, like DagNode.tm)."""
  tm = node.tm or IDENT_TM
  return tm if node.parent is None else mul_tm(node_wtm(node.parent), tm)


def mul_tm(a, b):
  """Composes rows-as-axes tms: result = a * b (b is local to a)."""
  def xform_dir(v):
    return tuple(v[0] * a[0][i] + v[1] * a[1][i] + v[2] * a[2][i] for i in range(3))
  rows = [xform_dir(b[0]), xform_dir(b[1]), xform_dir(b[2])]
  t = xform_dir(b[3])
  rows.append(tuple(t[i] + a[3][i] for i in range(3)))
  return rows
