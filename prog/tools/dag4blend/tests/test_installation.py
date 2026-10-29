"""Build and enable the complete archive in an isolated Blender script path."""
import os
from pathlib import Path
import runpy
import sys
import struct
import subprocess
import tempfile
import zipfile

import addon_utils
import bpy

ROOT = Path(__file__).resolve().parents[1]
builder = runpy.run_path(str(ROOT / '__build_pack.py'))
with tempfile.TemporaryDirectory(prefix='dag4blend-install-test-', dir=ROOT / 'tests') as temporary:
    temporary = Path(temporary)
    assert temporary.resolve().is_relative_to(ROOT / 'tests')
    archive = builder['main'](['--output', str(temporary / 'dag4blend.zip')])
    scripts = temporary / 'scripts'
    addons = scripts / 'addons'
    addons.mkdir(parents=True)
    with zipfile.ZipFile(archive) as packaged:
        assert packaged.testzip() is None
        assert 'dag4blend/animation.py' in packaged.namelist()
        assert 'dag4blend/lights.py' in packaged.namelist()
        assert not any('__pycache__' in name or '/tests/' in name for name in packaged.namelist())
        packaged.extractall(addons)
    os.environ['BLENDER_USER_SCRIPTS'] = str(scripts)
    sys.path.insert(0, str(addons))
    bpy.utils.refresh_script_paths()
    addon_utils.enable('dag4blend', default_set=True)
    assert addon_utils.check('dag4blend')[1], 'Full add-on failed to register'
    assert hasattr(bpy.types.Scene, 'dag4blend')
    assert bpy.ops.export_scene.dagor_a2d.get_rna_type().identifier == 'EXPORT_SCENE_OT_dagor_a2d'
    assert bpy.ops.dt.uv_channel.get_rna_type().identifier == 'DT_OT_uv_channel'
    preferences = bpy.context.preferences.addons['dag4blend'].preferences
    project = preferences.projects.add()
    project.name = 'test project'
    project.path = str(temporary)
    preferences.project_active = '0'
    # Exercise the real exporter with an armature modifier, not extracted
    # methods. Selecting the mesh alone must bring its skeleton into the DAG.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.object.armature_add()
    rig = bpy.context.object
    rig.name = 'test_rig'
    rig.data.bones[0].name = 'test_joint'
    bpy.ops.object.mode_set(mode='EDIT')
    tip = rig.data.edit_bones.new('test_tip')
    tip.head, tip.tail = (0, 1, 0), (0, 2, 0)
    tip.parent = rig.data.edit_bones['test_joint']
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.mode_set(mode='POSE')
    rig.data.bones.active = rig.data.bones['test_joint']
    bpy.ops.pose.select_all(action='SELECT')
    bone_text = bpy.data.texts.new('dagor_bone_properties')
    bone_text.write('label:t="Bone Script"; animated_node:b=yes')
    assert bpy.ops.dt.bone_properties(operation='APPLY') == {'FINISHED'}
    assert all('Bone Script' in bone['dagor_script'] for bone in rig.data.bones), [(bone.name, bone.get('dagor_script')) for bone in rig.data.bones]
    assert bpy.ops.dt.bone_properties(operation='COPY') == {'FINISHED'}
    assert bpy.ops.dt.bone_properties(operation='CLEAR') == {'FINISHED'}
    assert all(bone['dagor_script'] == '' for bone in rig.data.bones)
    assert bpy.ops.dt.bone_properties(operation='APPLY') == {'FINISHED'}
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.location = (5, 7, 9)
    rig.rotation_euler = (0.2, 0.3, 0.4)
    rig.scale = (1.5, 1, 0.75)
    bpy.ops.mesh.primitive_cube_add()
    mesh_obj = bpy.context.object
    mesh_obj.name = 'test_skin'
    script_text = 'Case Sensitive = File; "Quoted" ~ Tilde'
    mesh_obj.dagorprops['description:t'] = script_text
    group = mesh_obj.vertex_groups.new(name='test_joint')
    group.add(list(range(len(mesh_obj.data.vertices))), 0.5, 'REPLACE')
    tip_group = mesh_obj.vertex_groups.new(name='test_tip')
    tip_group.add(list(range(len(mesh_obj.data.vertices))), 0.5, 'REPLACE')
    modifier = mesh_obj.modifiers.new('Skin', 'ARMATURE')
    modifier.object = rig
    attachment = bpy.data.objects.new('test_attachment', None)
    bpy.context.collection.objects.link(attachment)
    attachment.parent = rig
    attachment.parent_type = 'BONE'
    attachment.parent_bone = 'test_tip'
    attachment.location = (0.2, 0.3, 0.4)
    bpy.context.view_layer.update()
    attachment_world = attachment.matrix_world.copy()
    mesh_obj.data.polygons.foreach_set('use_smooth', [True] * len(mesh_obj.data.polygons))
    material = bpy.data.materials.new('test_material')
    material.dagormat.shader_class = 'gi_black'
    mesh_obj.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    attachment.select_set(True)
    bpy.context.view_layer.objects.active = mesh_obj
    assert bpy.ops.dt.generate_lods(count=1, ratio=0.5, collision=False) == {'FINISHED'}
    skinned_lod = bpy.data.objects['test_skin.lod01']
    assert skinned_lod.modifiers[0].type == 'ARMATURE' and skinned_lod.modifiers[0].object == rig
    assert 'test_joint' in skinned_lod.vertex_groups
    assert all(vertex.groups for vertex in skinned_lod.data.vertices)
    export_path = temporary / 'skin.dag'
    original_objects = set(bpy.data.objects)
    original_meshes = set(bpy.data.meshes)
    assert bpy.ops.export_scene.dag(filepath=str(export_path), limits='Sel.Joined') == {'FINISHED'}
    assert export_path.is_file()
    assert set(bpy.data.objects) == original_objects
    assert set(bpy.data.meshes) == original_meshes
    assert not list(temporary.glob('.dag4blend-*'))
    data = export_path.read_bytes()
    assert struct.unpack_from('<I', data)[0] == 0x1A474144
    assert b'test_joint' in data and b'dagor_bone:b=yes' in data
    repository = ROOT.parents[2]
    tools = repository / 'tools/dagor_cdk/windows-x86_64'
    engine_assets = temporary / 'engine-assets'
    engine_assets.mkdir()
    (engine_assets / 'skin.dag').write_bytes(data)
    (engine_assets / 'skin.skeleton.blk').write_text('name:t="skin.dag"\n')
    shaders = (repository / 'tools/dargbox/shaders/game').as_posix()
    plugin = (tools / 'plugins/dabuild/modelExp-dev.dll').as_posix()
    app = temporary / 'application.blk'
    app.write_text('shadersAbs:t="' + shaders + '''"
assets {
 base:t="engine-assets"
 types { type:t="skeleton" }
 export {
  types { type:t="skeleton" }
  plugins { plugin:t="''' + plugin + '''" }
  cache:t="engine-cache"
  assetCache:t="engine-asset-cache"
  destination { PC:t="engine-res" }
 }
}
''')
    engine = subprocess.run([str(tools / 'daBuild-dev.exe'), '-target:PC', '-nopbar',
                             '-build:skin:skeleton.bin', str(app)], cwd=temporary,
                            capture_output=True, text=True, timeout=60,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    print(engine.stdout)
    assert engine.returncode == 0, engine.stdout + engine.stderr
    assert (temporary / 'skeleton.bin').is_file()
    a2d_path = temporary / 'skin.a2d'
    rig.select_set(True)
    assert bpy.ops.export_scene.dagor_a2d(filepath=str(a2d_path), start=0, end=2) == {'FINISHED'}
    assert a2d_path.read_bytes()[:4] == b'ANIM'
    original_scene = bpy.context.scene
    assert bpy.ops.import_scene.dag(filepath=str(export_path), with_lods=False) == {'FINISHED'}
    imported_collection = bpy.data.collections['skin']
    imported_mesh = next(obj for obj in imported_collection.objects if obj.type == 'MESH')
    assert imported_mesh.dagorprops['description:t'] == script_text
    imported_rig = next(obj for obj in imported_collection.objects if obj.type == 'ARMATURE')
    print('Imported skeleton:', imported_rig.name, list(imported_rig.data.bones.keys()))
    assert imported_mesh.modifiers[0].type == 'ARMATURE'
    assert imported_mesh.modifiers[0].object == imported_rig
    assert 'test_joint' in imported_rig.data.bones
    assert imported_rig.data.bones['test_tip'].parent == imported_rig.data.bones['test_joint']
    assert 'test_joint' in imported_mesh.vertex_groups
    imported_attachment = next(obj for obj in imported_collection.objects if obj.name.startswith('test_attachment'))
    assert imported_attachment.parent == imported_rig and imported_attachment.parent_type == 'BONE'
    assert imported_attachment.parent_bone == 'test_tip'
    bpy.context.view_layer.update()
    assert max(abs(imported_attachment.matrix_world[i][j] - attachment_world[i][j])
               for i in range(4) for j in range(4)) < 1e-4
    weights = [vertex.groups[0].weight for vertex in imported_mesh.data.vertices]
    assert len(weights) == 8 and all(abs(weight - 0.5) < 1e-6 for weight in weights)
    rig.pose.bones['test_joint'].location = (0.5, 0, 0)
    imported_rig.pose.bones['test_joint'].location = (0.5, 0, 0)
    with bpy.context.temp_override(scene=original_scene, view_layer=original_scene.view_layers[0]):
        bpy.context.view_layer.update()
        evaluated = mesh_obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        expected_points = [mesh_obj.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
    bpy.context.view_layer.update()
    evaluated = imported_mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    actual_points = [imported_mesh.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
    assert max((actual - expected).length for actual, expected in zip(actual_points, expected_points)) < 1e-4
    bpy.ops.object.select_all(action='DESELECT')
    imported_mesh.select_set(True)
    bpy.context.view_layer.objects.active = imported_mesh
    original_uvs = [tuple(loop.uv) for loop in imported_mesh.data.uv_layers[0].data]
    assert bpy.ops.dt.uv_atlas(mode='UNWRAP', target=2) == {'FINISHED'}
    assert len(imported_mesh.data.uv_layers) == 2
    assert [tuple(loop.uv) for loop in imported_mesh.data.uv_layers[0].data] == original_uvs
    assert bpy.ops.dt.uv_atlas(mode='PACK', source=2, target=3) == {'FINISHED'}
    assert len(imported_mesh.data.uv_layers) == 3
    assert bpy.ops.dt.convert_materials(to_dagor=False) == {'FINISHED'}
    assert imported_mesh.active_material.use_nodes
    assert bpy.ops.dt.convert_materials(to_dagor=True, shader='gi_black') == {'FINISHED'}
    assert imported_mesh.active_material.dagormat.shader_class == 'gi_black'
    deformed = imported_mesh.copy()
    deformed.data = imported_mesh.data.copy()
    imported_collection.objects.link(deformed)
    bpy.context.view_layer.update()
    for vertex in deformed.data.vertices:
        vertex.co.x += 1
    deformed.select_set(True)
    assert bpy.ops.dt.deformation_colors(configure_materials=False) == {'FINISHED'}
    assert abs(imported_mesh['dagor_deform_max_height'] - 2) < 1e-6
    assert imported_mesh.data.color_attributes['DEFORM'].data[0].color_srgb[0] < 1e-5
    assert bpy.ops.dt.fix_normal_orientation() == {'FINISHED'}
    # Cursor-space clipping and shader-compatible Pivot Painter data.
    from dag4blend.tools import decal_projector, pivot_painter, ao_baker
    deform_before = [tuple(value.color_srgb) for value in imported_mesh.data.color_attributes['DEFORM'].data]
    ao_baker.bake_ao(bpy.context, [imported_mesh], [imported_mesh], samples=8)
    assert [tuple(value.color_srgb) for value in imported_mesh.data.color_attributes['DEFORM'].data] == deform_before
    assert imported_mesh.data.color_attributes.active_color.name == 'AO'
    bpy.ops.mesh.primitive_plane_add(size=4)
    plane = bpy.context.object
    plane.data.normals_split_custom_set([(0, 0, 1)] * len(plane.data.loops))
    ao_baker.bake_ao(bpy.context, [plane], [plane], samples=16)
    assert all(value.color_srgb[0] > 0.999 for value in plane.data.color_attributes[0].data)
    assert plane.data.attributes.get('dagor_map_8') is not None
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0.2))
    roof = bpy.context.object
    bpy.context.view_layer.update()
    ao_baker.bake_ao(bpy.context, [plane], [plane, roof], samples=16, distance=2, channel='R')
    assert all(value.color_srgb[0] < 0.2 and value.color_srgb[1] > 0.999
               for value in plane.data.color_attributes[0].data)
    bpy.ops.object.select_all(action='DESELECT')
    plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    ao_path = temporary / 'ao.dag'
    assert bpy.ops.export_scene.dag(filepath=str(ao_path), limits='Sel.Joined') == {'FINISHED'}
    assert bpy.ops.import_scene.dag(filepath=str(ao_path), with_lods=False) == {'FINISHED'}
    imported_ao = next(obj for obj in bpy.data.collections['ao'].objects if obj.type == 'MESH')
    assert imported_ao.data.attributes.get('dagor_map_8') is not None
    for value in imported_ao.data.attributes['dagor_map_8'].data:
        assert value.vector.x < 0.2 and value.vector.y > 0.999 and value.vector.z > 0.999
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.context.scene.cursor.rotation_euler = (0, 0, 0)
    assert bpy.ops.dt.project_decal(target_name=plane.name, width=1, height=1, depth=1) == {'FINISHED'}
    decal = decal_projector.project_decal(bpy.context, plane, 1, 1, 1)
    assert decal.data.polygons
    assert all(abs(vertex.co.x) <= 0.50001 and abs(vertex.co.y) <= 0.50001
               and abs(vertex.co.z - 0.001) < 1e-5 for vertex in decal.data.vertices)
    convex = decal_projector.project_decal(bpy.context, plane, 1, 1, 1,
                                           convex=[(0, 0), (1, 0), (0, 1)])
    assert all(vertex.co.x + vertex.co.y <= 1e-5 for vertex in convex.data.vertices)
    root = bpy.data.objects.new('tree', None)
    bpy.context.collection.objects.link(root)
    root.location = (10, 20, 30)
    for index in range(2):
        bpy.ops.mesh.primitive_cube_add()
        branch = bpy.context.object
        branch.name = f'branch{index}'
        branch.parent = root
        branch.location = (index, 0, 2)
    bpy.context.view_layer.update()
    nodes, indices, positions, directions = pivot_painter.hierarchy_data(root)
    assert positions[1] == (0, 2, 0, 0)
    assert directions[1][1] == 1
    wind = pivot_painter.paint_hierarchy(bpy.context, root, str(temporary / 'pivot'))
    assert len(wind.data.vertices) == 16
    for loop in wind.data.uv_layers[3].data:
        u, v = loop.uv
        index = int(u * 32) + int((1 - v) * 64) * 32
        assert index in (1, 2)
    pos_dds = (temporary / 'pivot/pivot_pos.dds').read_bytes()
    dir_dds = (temporary / 'pivot/pivot_dir.dds').read_bytes()
    assert len(pos_dds) == 148 + 2048 * 8 and len(dir_dds) == 148 + 2048 * 4
    assert pos_dds[:4] == b'DDS ' and struct.unpack_from('<I', pos_dds, 128)[0] == 10
    assert struct.unpack_from('<4e', pos_dds, 148 + 8) == positions[1]
    bpy.ops.curve.primitive_nurbs_path_add()
    path_object = bpy.context.object
    path_object.name = 'test_path'
    path_object.data.bevel_depth = 0.2
    path_object.dagorprops['curve_label:t'] = 'Curve = Case; Test'
    original_curve_count, original_object_count = len(bpy.data.curves), len(bpy.data.objects)
    curve_path = temporary / 'curve.dag'
    assert bpy.ops.export_scene.dag(filepath=str(curve_path), limits='Sel.Joined') == {'FINISHED'}
    assert len(bpy.data.curves) == original_curve_count and len(bpy.data.objects) == original_object_count
    assert path_object.data.bevel_depth > 0.19
    assert bpy.ops.import_scene.dag(filepath=str(curve_path), with_lods=False) == {'FINISHED'}
    imported_curve = next(obj for obj in bpy.data.collections['curve'].objects if obj.type == 'CURVE')
    assert imported_curve.dagorprops['curve_label:t'] == 'Curve = Case; Test'
    assert imported_curve.data.dimensions == '3D'
    assert len(imported_curve.data.splines[0].bezier_points) > len(path_object.data.splines[0].points)
    legacy_collections = []
    for name, object_name in [('LOD00', 'legacy_base'), ('DMG_LOD00', 'legacy_damage')]:
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        collection.objects.link(bpy.data.objects.new(object_name, None))
        legacy_collections.append(collection)
    bpy.context.view_layer.update()
    assert bpy.ops.export_scene.dag(filepath=str(temporary / 'legacy.lod00.dag'), limits='Legacy') == {'FINISHED'}
    assert b'legacy_base' in (temporary / 'legacy.lod00.dag').read_bytes()
    assert b'legacy_damage' in (temporary / 'legacy_dmg.lod00.dag').read_bytes()
    damage_layer = next(layer for layer in bpy.context.view_layer.layer_collection.children
                        if layer.collection == legacy_collections[1])
    damage_layer.hide_viewport = True
    bpy.context.view_layer.update()
    assert bpy.ops.export_scene.dag(filepath=str(temporary / 'visible_legacy.lod00.dag'), limits='Legacy') == {'FINISHED'}
    assert not (temporary / 'visible_legacy_dmg.lod00.dag').exists()
    assert bpy.ops.export_scene.dag(filepath=str(temporary / 'hidden_legacy.lod00.dag'), limits='Legacy', include_hidden=True) == {'FINISHED'}
    assert (temporary / 'hidden_legacy_dmg.lod00.dag').is_file()
    export_props = bpy.data.scenes[0].dag4blend.exporter
    export_props.collection = legacy_collections[0]
    assert bpy.ops.export_scene.dag(filepath=str(temporary / 'ignored.dag'), limits='Col.Joined') == {'FINISHED'}
    assert (temporary / 'LOD00.dag').is_file() and not (temporary / 'ignored.dag').exists()
    export_props.collection = None
    native_fixture = temporary / 'native_inst.dag'
    native_fixture.write_bytes((repository / 'prog/tools/dagUtils/dagConvInst/inst.dag').read_bytes())
    assert bpy.ops.import_scene.dag(filepath=str(native_fixture), with_lods=False) == {'FINISHED'}
    assert bpy.data.collections['native_inst'].objects
    bpy.ops.mesh.primitive_cube_add()
    chunk = bpy.context.object
    chunk.name = 'damage_chunk'
    chunk.data.materials.append(material)
    generated = {}
    for shape in ('BOX', 'SPHERE', 'CAPSULE', 'CONVEX'):
        before = set(bpy.data.objects)
        assert bpy.ops.dt.setup_damage(shape=shape, maximum=8, offset=0.01) == {'FINISHED'}
        collider = next(iter(set(bpy.data.objects) - before))
        assert collider.parent == chunk
        assert collider.dagorprops['collision:t'] == shape.lower()
        assert collider.dagorprops['collType:t'] == ('none' if shape == 'CONVEX' else shape.lower())
        if shape == 'CONVEX':
            assert len(collider.data.vertices) <= 8
        collider.data.materials.append(material)
        generated[shape] = collider
    assert chunk.dagorprops['physObj:b'] is True
    for shape, asset_type, plugin_name in [('BOX', 'physObj', 'phObjExp-dev.dll'),
                                           ('CONVEX', 'collision', 'collisionExp-dev.dll')]:
        damage_assets = temporary / ('damage-assets-' + shape.lower())
        damage_assets.mkdir()
        bpy.ops.object.select_all(action='DESELECT')
        chunk.select_set(True)
        generated[shape].select_set(True)
        bpy.context.view_layer.objects.active = chunk
        dag_path = damage_assets / f'damage_{shape.lower()}.dag'
        assert bpy.ops.export_scene.dag(filepath=str(dag_path), limits='Sel.Joined') == {'FINISHED'}
        name = 'damage_' + shape.lower()
        (damage_assets / f'{name}.{asset_type}.blk').write_text(f'name:t="{dag_path.name}"\nsimplePhysObj:b=yes\n')
        app = temporary / f'application_{shape.lower()}.blk'
        plugin = (tools / 'plugins/dabuild' / plugin_name).as_posix()
        app.write_text('assets { base:t="' + damage_assets.name + '" types { type:t="' + asset_type +
            '" } export { types { type:t="' + asset_type + '" } plugins { plugin:t="' + plugin +
            '" } cache:t="damage-cache" assetCache:t="damage-asset-cache" destination { PC:t="damage-res" } } }')
        result = subprocess.run([str(tools / 'daBuild-dev.exe'), '-target:PC', '-nopbar',
            f'-build:{name}:{name}.bin', str(app)], cwd=temporary, capture_output=True, text=True,
            timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        print(result.stdout)
        assert result.returncode == 0, result.stdout + result.stderr
        assert (temporary / f'{name}.bin').is_file()
    addon_utils.disable('dag4blend', default_set=True)
    assert not addon_utils.check('dag4blend')[1]
print('PASS: recursive archive, bundled dependencies, full add-on enable/disable')
