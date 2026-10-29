"""Run with Blender --background --factory-startup --python this_file."""
import ast
import importlib.util
import io
import math
from pathlib import Path
import runpy
import struct
import sys

import bpy
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dagor_test_lights', ROOT / 'lights.py')
lights = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = lights
spec.loader.exec_module(lights)


def close(actual, expected):
    assert abs(actual - expected) < 1e-5, (actual, expected)


# Independently constructed packed fixture, using the field order and byte
# packing of Max's DagLight + DagLight2 (21 + 13 bytes, no alignment padding).
fixture = struct.pack('<5fBB3f', 2, 1, 0.5, 100, 5, 2, 1, 30, 45, 2)
data = lights.DagLight.from_bytes(fixture)
assert data.to_bytes() == fixture
assert data.type == 1 and data.hotspot == 30 and data.falloff == 45
legacy = lights.DagLight.from_bytes(fixture[:21])
assert legacy.type == 0 and legacy.intensity == 2
for bad in (b'', fixture[:-1], fixture + b'\0'):
    try:
        lights.DagLight.from_bytes(bad)
        raise AssertionError('Invalid payload accepted')
    except ValueError:
        pass

environment = runpy.run_path(str(ROOT / 'tests/test_export_hierarchy.py'))
ns = environment['namespace']
ns.update(DagLight=lights.DagLight, LIGHT_TYPES=lights.LIGHT_TYPES)
ns['SUPPORTED_TYPES'] = ('MESH', 'CURVE', 'EMPTY', 'LIGHT')
exec((ROOT / 'dagMath.py').read_text(), ns)
reader_source = (ROOT / 'importer/reader.py').read_text()
exec('\n'.join(line for line in reader_source.splitlines()
               if not line.startswith('from ..')), ns)
tree = ast.parse((ROOT / 'importer/importer.py').read_text())
importer = next(node for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == 'DagImporter')
importer.bases = []
importer.body = [node for node in importer.body if isinstance(node, ast.FunctionDef)
                 and node.name in {'loadObj', 'importNodes', 'buildLight', 'buildEmpty'}]
exec(compile(ast.fix_missing_locations(ast.Module(body=[importer], type_ignores=[])),
             '<importer methods>', 'exec'), ns)

for kind in lights.LIGHT_TYPES:
    source = bpy.data.lights.new('source ' + kind, kind)
    source.color = (1.0, 0.5, 0.25)
    source.energy = 2
    source.use_custom_distance = True
    source.cutoff_distance = 100
    source['dagor_decay_radius'] = 5.0
    source['dagor_decay'] = 2
    if kind == 'SPOT':
        source.spot_size = math.radians(45)
        source.spot_blend = 1 / 3
    obj = bpy.data.objects.new('light ' + kind, source)
    bpy.context.collection.objects.link(obj)
    obj.matrix_world = Matrix.Translation((3, 5, 7)) @ Matrix.Rotation(0.4, 4, 'Y')
    child = bpy.data.objects.new('child of ' + kind, None)
    bpy.context.collection.objects.link(child)
    child.parent = obj
    child.location = (1, 2, 3)
    bpy.context.view_layer.update()
    exporter = ns['DagExporter']()
    exporter.nodes, exporter.last_index = [], 0
    exporter.gatherObjPropScript = lambda obj, node: 'tag:t="light fixture"'
    root = ns['NodeExp']()
    root.id, root.parent_id = 65535, -1
    assert exporter.enumerate([obj, child], [obj], root, bpy.context.scene) == 0
    exporter.writer = ns['DagWriter']()
    exporter.writer.file = io.BytesIO()
    exporter.saveNodes(root)
    importer = ns['DagImporter']()
    importer.end = False
    importer.reader = ns['DagReader']()
    importer.reader.file = io.BytesIO(exporter.writer.file.getvalue())
    importer.reader.eof = False
    chunk = importer.reader.beginChunk()
    parsed_root = importer.importNodes(chunk.size)
    parsed = parsed_root.children[0]
    assert parsed.light is not None and len(parsed.children) == 1
    assert parsed.light.type == lights.LIGHT_TYPES.index(kind)
    assert parsed.objProps == 'tag:t="light fixture"'
    importer.collection = bpy.data.collections.new('imported ' + kind)
    bpy.context.scene.collection.children.link(importer.collection)
    importer.buildMesh = importer.buildCurves = lambda *args: None
    importer.buildObjProperties = lambda obj, props: obj.__setitem__('fixture_script', props)
    tm = parsed.tm.transposed()
    tm[1], tm[2] = tm[2].copy(), tm[1].copy()
    importer.buildLight(parsed, tm, None)
    imported = next(o for o in importer.collection.objects if o.type == 'LIGHT')
    imported_child = next(o for o in importer.collection.objects if o.type == 'EMPTY')
    assert imported_child.parent == imported
    bpy.context.view_layer.update()
    environment['assert_matrix'](imported.matrix_world, obj.matrix_world)
    environment['assert_matrix'](imported_child.matrix_world, child.matrix_world)
    roundtrip = lights.DagLight.from_blender(imported.data)
    expected = lights.DagLight.from_blender(source)
    for actual, target in zip(struct.unpack('<5fBB3f', roundtrip.to_bytes()),
                              struct.unpack('<5fBB3f', expected.to_bytes())):
        close(actual, target)

area = bpy.data.lights.new('unsupported area', 'AREA')
try:
    lights.DagLight.from_blender(area)
    raise AssertionError('Area lights must not be silently converted')
except ValueError:
    pass
for fixture in (lights.DagLight((10, 2, 0.5), 100, 1, 2, 1, 180, 270, 0.25),
                lights.DagLight((-1, -0.5, 0), -1, 1, 0, 0, 0, 0, -2)):
    preview = bpy.data.lights.new('clamped fixture', lights.LIGHT_TYPES[fixture.type])
    fixture.apply_to_blender(preview)
    assert lights.DagLight.from_blender(preview).to_bytes() == fixture.to_bytes()
print('PASS: Max light fixture, legacy format, invalid payloads, all light types, DAG roundtrip, child transforms')
