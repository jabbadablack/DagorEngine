# Round-trip test for dag4blend armature + skin export.
#   python test_armature_export.py [path/to/blender.exe]
# Installs the add-on from this source tree into a temporary user scripts folder, runs headless Blender to build and
# export a small skinned rig, then validates the .dag with pythonCommon/dag_reader.py.
import json
import os
import shutil
import subprocess
import sys
import tempfile

try:
  import bpy
except ImportError:
  bpy = None

ADDON_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PYTHON_COMMON = os.path.join(os.path.dirname(ADDON_DIR), 'pythonCommon')
DEFAULT_BLENDER = r'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
EPS = 1e-4


# ---------------------------------------------------------------- inside Blender

def build_scene():
  from mathutils import Matrix, Euler
  bpy.ops.object.select_all(action='SELECT')
  bpy.ops.object.delete()

  arm_data = bpy.data.armatures.new('rig')
  rig = bpy.data.objects.new('rig', arm_data)
  bpy.context.scene.collection.objects.link(rig)
  rig.location = (1.0, 2.0, 0.5)
  rig.rotation_euler = Euler((0.0, 0.0, 0.5))
  bpy.context.view_layer.objects.active = rig
  bpy.ops.object.mode_set(mode='EDIT')
  eb = arm_data.edit_bones

  def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name)
    b.head, b.tail = head, tail
    b.parent = eb[parent] if parent else None
    b.use_deform = deform
    return b

  bone('hips', (0, 0, 0), (0, 0, 0.5))
  bone('ctrl', (0, 0, 0.5), (0, 0.3, 0.5), 'hips', deform=False)   # control bone between deform bones: skipped
  bone('spine', (0, 0, 0.5), (0, 0, 1.0), 'ctrl')
  bone('head', (0, 0, 1.0), (0.1, 0, 1.4), 'spine').roll = 0.3
  bone('ik_target', (0.5, 0, 0), (0.5, 0, 0.3), deform=False)       # non-deform root: skipped
  bpy.ops.object.mode_set(mode='OBJECT')

  bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0.7))
  body = bpy.context.active_object
  body.name = 'body'
  body.scale = (0.3, 0.3, 1.4)
  bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
  mat = bpy.data.materials.new('body_mat')
  mat.dagormat['shader_class'] = 'dynamic_simple'
  body.data.materials.append(mat)
  body.parent = rig
  body.matrix_parent_inverse = rig.matrix_world.inverted()
  mod = body.modifiers.new('Armature', 'ARMATURE')
  mod.object = rig
  groups = {name: body.vertex_groups.new(name=name) for name in ('hips', 'spine', 'head', 'ctrl')}
  for v in body.data.vertices:
    z = (body.matrix_world @ v.co).z
    if z < 0.5:
      groups['hips'].add([v.index], 0.6, 'REPLACE')   # unnormalized: exporter must normalize to 0.5/0.5
      groups['spine'].add([v.index], 0.6, 'REPLACE')
      groups['ctrl'].add([v.index], 1.0, 'REPLACE')   # non-deform group: ignored
    else:
      groups['head'].add([v.index], 1.0, 'REPLACE')

  # a posed rig must still export its rest pose (armature modifier is not applied)
  rig.pose.bones['spine'].rotation_mode = 'XYZ'
  rig.pose.bones['spine'].rotation_euler = (0.7, 0.0, 0.0)
  bpy.context.view_layer.update()
  return rig, body


def export(path, objs):
  bpy.ops.object.select_all(action='DESELECT')
  for o in objs:
    o.select_set(True)
  bpy.context.view_layer.objects.active = objs[0]
  return bpy.ops.export_scene.dag(filepath=path, limits='Sel.Joined', modifiers=True)


def blender_main(out_dir):
  import addon_utils
  from mathutils import Matrix
  addon_utils.enable('dag4blend', default_set=True)
  rig, body = build_scene()
  swap = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
  expected = {
    'bones': {},
    'rest_vertices': [list(swap @ body.matrix_world @ v.co) for v in body.data.vertices],
    'export_ok': list(export(os.path.join(out_dir, 'ok.dag'), [rig, body])),
  }
  for b in rig.data.bones:
    m = (swap @ rig.matrix_world @ b.matrix_local).transposed()
    expected['bones'][b.name] = [list(m[i])[:3] for i in range(4)]

  # unweighted vertex: export must be cancelled and must not write the file
  body.vertex_groups['head'].remove([body.data.vertices[-1].index])
  expected['export_bad'] = list(export(os.path.join(out_dir, 'bad.dag'), [rig, body]))
  with open(os.path.join(out_dir, 'expected.json'), 'w') as f:
    json.dump(expected, f)


# ---------------------------------------------------------------- outside Blender

def close(a, b):
  return all(abs(x - y) < EPS for x, y in zip(a, b))


def close_tm(a, b):
  return all(close(ra, rb) for ra, rb in zip(a, b))


def transform_point(tm, p):
  return [p[0] * tm[0][i] + p[1] * tm[1][i] + p[2] * tm[2][i] + tm[3][i] for i in range(3)]


def validate(out_dir):
  sys.path.insert(0, PYTHON_COMMON)
  from dag_reader import read_dag, node_wtm
  with open(os.path.join(out_dir, 'expected.json')) as f:
    expected = json.load(f)
  failures = []

  def check(cond, msg):
    if not cond:
      failures.append(msg)

  check(expected['export_ok'] == ['FINISHED'], f'valid export returned {expected["export_ok"]}')
  check(expected['export_bad'] == ['CANCELLED'], f'export with unweighted vertex returned {expected["export_bad"]}')
  check(not os.path.exists(os.path.join(out_dir, 'bad.dag')), 'cancelled export still wrote bad.dag')

  root = read_dag(os.path.join(out_dir, 'ok.dag'))
  nodes = {n.name: n for n in root.walk() if n.parent is not None}
  check(sorted(nodes) == ['body', 'head', 'hips', 'rig', 'spine'], f'unexpected nodes {sorted(nodes)}')
  parents = {name: n.parent.name for name, n in nodes.items()}
  check(parents.get('rig') == '' and parents.get('hips') == 'rig' and parents.get('spine') == 'hips' and
        parents.get('head') == 'spine' and parents.get('body') == 'rig', f'unexpected hierarchy {parents}')
  for name in ('hips', 'spine', 'head'):
    n = nodes.get(name)
    if n is None:
      continue
    check('animated_node:b=yes' in n.script, f'{name}: script {n.script!r} lacks animated_node')
    check(n.flags == 0 and n.vertices is None, f'{name}: bone node must be a non-renderable helper')
    check(close_tm(node_wtm(n), expected['bones'][name]), f'{name}: node world tm differs from Blender rest matrix')

  body = nodes.get('body')
  if body is not None and body.bones is not None:
    ids = {n.id: n.name for n in nodes.values()}
    names = [ids.get(i) for i, _ in body.bones]
    check(names == ['hips', 'spine', 'head'], f'skin bones {names}')
    for (i, bind), name in zip(body.bones, names):
      if name:
        check(close_tm(bind, expected['bones'][name]), f'{name}: bind tm differs from rest world tm')
    vc = len(body.vertices)
    check(vc == len(expected['rest_vertices']), f'vertex count {vc}')
    body_wtm = node_wtm(body)
    for v, (local, rest) in enumerate(zip(body.vertices, expected['rest_vertices'])):
      check(close(transform_point(body_wtm, local), rest), f'vertex {v}: not exported in rest pose')
    check(len(body.weights) == vc * len(body.bones), 'weights size mismatch')
    for v in range(vc):
      w = [body.weights[b * vc + v] for b in range(len(body.bones))]
      check(abs(sum(w) - 1.0) < EPS, f'vertex {v}: weights {w} do not sum to 1')
      check(close(w, [0.5, 0.5, 0.0]) or close(w, [0.0, 0.0, 1.0]), f'vertex {v}: unexpected weights {w}')
  else:
    check(False, 'body has no BONES chunk')

  for f in failures:
    print('FAIL:', f)
  print('PASS' if not failures else f'{len(failures)} failure(s)')
  return not failures


def install_addon(scripts_dir):
  dst = os.path.join(scripts_dir, 'addons', 'dag4blend')
  shutil.copytree(ADDON_DIR, dst, ignore=shutil.ignore_patterns('tests', 'additional', '*.zip', '__pycache__'))
  for f in ('datablock.py', 'pyparsing.py'):  # same files __build_pack.py bundles
    shutil.copy2(os.path.join(PYTHON_COMMON, f), dst)


def main():
  blender = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BLENDER
  with tempfile.TemporaryDirectory(prefix='dag4blend_test_') as tmp:
    scripts = os.path.join(tmp, 'scripts')
    install_addon(scripts)
    out_dir = os.path.join(tmp, 'out')
    os.makedirs(out_dir)
    env = dict(os.environ, BLENDER_USER_SCRIPTS=scripts)
    proc = subprocess.run([blender, '--background', '--factory-startup', '--python-exit-code', '1',
                           '--python', os.path.abspath(__file__), '--', out_dir],
                          env=env, capture_output=True, text=True)
    if proc.returncode != 0 or not os.path.exists(os.path.join(out_dir, 'expected.json')):
      print(proc.stdout[-4000:], proc.stderr[-4000:])
      print('FAIL: blender run failed')
      return 1
    return 0 if validate(out_dir) else 1


if __name__ == '__main__':
  if bpy is not None:
    blender_main(sys.argv[sys.argv.index('--') + 1])
  else:
    sys.exit(main())
