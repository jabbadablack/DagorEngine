"""Roundtrip real sample assets when optional sample content is installed."""
import os
from pathlib import Path
import runpy
import sys
import tempfile
import zipfile

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
patterns = [
    ('samples', '**/sponza.dag'),
    ('samples', '**/tree_tilia_large_a.lod00.dag'),
    ('outerSpace', '**/water_mining_zarya.lod00.dag'),
    ('outerSpace', '**/tree_sample_betula_ermanii_small_a.collision.dag'),
    ('outerSpace', '**/sample_rock_big_a.lod00.dag'),
]
fixtures = []
for directory, pattern in patterns:
    matches = sorted((REPOSITORY / directory).glob(pattern))
    if matches:
        fixtures.append(matches[0])
if not fixtures:
    print('SKIP: optional sample DAG content is not installed')
    sys.exit(0)


def signature(objects):
    meshes = [obj for obj in objects if obj.type == 'MESH']
    shaders = sorted({mat.dagormat.shader_class for obj in meshes for mat in obj.data.materials if mat})
    points = [obj.matrix_world @ vertex.co for obj in meshes for vertex in obj.data.vertices]
    for obj in meshes:
        obj.data.calc_loop_triangles()
    bounds = tuple(round(function(point[axis] for point in points), 3)
                   for function in (min, max) for axis in range(3))
    return (len(meshes), sum(len(obj.data.vertices) for obj in meshes),
            sum(len(obj.data.loop_triangles) for obj in meshes), bounds, shaders)


builder = runpy.run_path(str(ROOT / '__build_pack.py'))
with tempfile.TemporaryDirectory(prefix='dag4blend-samples-', dir=ROOT / 'tests') as temporary:
    temporary = Path(temporary)
    archive = builder['main'](['--output', str(temporary / 'addon.zip')])
    scripts = temporary / 'scripts'
    addons = scripts / 'addons'
    addons.mkdir(parents=True)
    with zipfile.ZipFile(archive) as package:
        package.extractall(addons)
    os.environ['BLENDER_USER_SCRIPTS'] = str(scripts)
    sys.path.insert(0, str(addons))
    bpy.utils.refresh_script_paths()
    addon_utils.enable('dag4blend', default_set=True)
    assert addon_utils.check('dag4blend')[1]
    preferences = bpy.context.preferences.addons['dag4blend'].preferences
    project = preferences.projects.add()
    project.name, project.path = 'sample compatibility', str(temporary)
    preferences.project_active = '0'
    for index, fixture in enumerate(fixtures):
        source = temporary / f'source_{index}.dag'
        source.write_bytes(fixture.read_bytes())
        before = set(bpy.data.objects)
        assert bpy.ops.import_scene.dag(filepath=str(source), with_lods=False) == {'FINISHED'}
        imported = set(bpy.data.objects) - before
        expected = signature(imported)
        assert expected[0] > 0, fixture
        bpy.ops.object.select_all(action='DESELECT')
        for obj in imported:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = next(iter(imported))
        output = temporary / f'roundtrip_{index}.dag'
        assert bpy.ops.export_scene.dag(filepath=str(output), limits='Sel.Joined') == {'FINISHED'}
        before = set(bpy.data.objects)
        assert bpy.ops.import_scene.dag(filepath=str(output), with_lods=False) == {'FINISHED'}
        actual = signature(set(bpy.data.objects) - before)
        assert actual == expected, (fixture, expected, actual)
        print(f'PASS: sample {fixture.relative_to(REPOSITORY)} geometry/bounds/shaders={actual}', flush=True)
    addon_utils.disable('dag4blend', default_set=True)
