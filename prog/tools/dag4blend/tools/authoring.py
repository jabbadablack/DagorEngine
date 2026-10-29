"""Blender-native batch LOD, collision and vegetation-normal workflows."""
import re
from fnmatch import fnmatchcase

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform


def selected_meshes(context):
    return [obj for obj in context.selected_objects if obj.type == 'MESH' and obj.data.is_editable]


def evaluated_mesh(context, obj):
    return bpy.data.meshes.new_from_object(obj.evaluated_get(context.evaluated_depsgraph_get()),
                                           preserve_all_data_layers=True,
                                           depsgraph=context.evaluated_depsgraph_get())


def generate_lods(context, source, count, ratio):
    if count <= 0:
        return []
    base = re.sub(r'\.lod\d\d$', '', source.name)
    group = bpy.data.collections.new(base + '.lods')
    context.scene.collection.children.link(group)
    base_collection = bpy.data.collections.new(base + '.lod00')
    group.children.link(base_collection)
    previous_collections = list(source.users_collection)
    base_collection.objects.link(source)
    for previous in previous_collections:
        previous.objects.unlink(source)
    result = []
    for index in range(1, count + 1):
        name = f'{base}.lod{index:02d}'
        collection = bpy.data.collections.new(name)
        group.children.link(collection)
        obj = source.copy()
        obj.name = name
        obj.data = source.data.copy()
        collection.objects.link(obj)
        obj.select_set(False)
        original_data = obj.data
        # Preserve linear skinning and vertex-group names on generated LODs.
        # Evaluate the rest geometry with only the copy's armature disabled.
        for modifier in obj.modifiers:
            if modifier.type == 'ARMATURE':
                modifier.show_viewport = False
        context.view_layer.update()
        obj.data = evaluated_mesh(context, obj)
        obj.modifiers.clear()
        if original_data.users == 0:
            bpy.data.meshes.remove(original_data)
        obj.matrix_world = source.matrix_world.copy()
        for key in source.dagorprops.keys() if hasattr(source, 'dagorprops') else ():
            obj.dagorprops[key] = source.dagorprops[key]
        modifier = obj.modifiers.new('Dagor LOD reduction', 'DECIMATE')
        modifier.ratio = ratio ** index
        modifier.use_collapse_triangulate = True
        with context.temp_override(object=obj, active_object=obj):
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        for original in source.modifiers:
            if original.type != 'ARMATURE':
                continue
            modifier = obj.modifiers.new(original.name, 'ARMATURE')
            for attribute in ('object', 'use_vertex_groups', 'use_bone_envelopes', 'use_deform_preserve_volume',
                              'vertex_group', 'invert_vertex_group', 'show_viewport', 'show_render'):
                setattr(modifier, attribute, getattr(original, attribute))
        result.append(obj)
    return result


def generate_collision(context, source, keep_materials='', remove_materials='', cut_height=None, properties=''):
    mesh = evaluated_mesh(context, source)
    bm = bmesh.new()
    try:
        keep = [pattern.strip().casefold() for pattern in keep_materials.split(',') if pattern.strip()]
        remove = [pattern.strip().casefold() for pattern in remove_materials.split(',') if pattern.strip()]
        eligible = set()
        for polygon in mesh.polygons:
            material = mesh.materials[polygon.material_index] if polygon.material_index < len(mesh.materials) else None
            name = material.name.casefold() if material else ''
            if (not keep or any(fnmatchcase(name, pattern) for pattern in keep)) and not any(fnmatchcase(name, pattern) for pattern in remove):
                eligible.update(polygon.vertices)
        if not eligible and not (keep or remove):
            eligible.update(range(len(mesh.vertices)))
        points = [mesh.vertices[index].co.copy() for index in eligible]
        if cut_height is not None:
            points = [point for point in points if point.z <= cut_height]
            for edge in mesh.edges:
                a, b = edge.vertices
                if a not in eligible or b not in eligible:
                    continue
                a, b = mesh.vertices[a].co, mesh.vertices[b].co
                if (a.z < cut_height < b.z) or (b.z < cut_height < a.z):
                    points.append(a.lerp(b, (cut_height - a.z) / (b.z - a.z)))
        # Start with points only: remove source interiors without retaining
        # duplicate/non-convex source faces in the collision hull.
        for point in points:
            bm.verts.new(point)
        if len(bm.verts) < 4:
            raise ValueError(f'{source.name}: a collision hull needs at least four points')
        hull = bmesh.ops.convex_hull(bm, input=list(bm.verts))
        unused = [element for element in hull['geom_interior'] + hull['geom_unused']
                  if isinstance(element, bmesh.types.BMVert) and element.is_valid]
        if unused:
            bmesh.ops.delete(bm, geom=list(set(unused)), context='VERTS')
        if not bm.faces or bm.calc_volume() <= 1e-12:
            raise ValueError(f'{source.name}: collision hull is empty')
        bm.to_mesh(mesh)
    except Exception:
        bpy.data.meshes.remove(mesh)
        raise
    finally:
        bm.free()
    mesh.materials.clear()
    name = re.sub(r'\.lod\d\d$', '', source.name) + '_collision'
    collection = bpy.data.collections.new(name)
    context.scene.collection.children.link(collection)
    obj = bpy.data.objects.new('Cls_' + re.sub(r'\.lod\d\d$', '', source.name), mesh)
    collection.objects.link(obj)
    obj.matrix_world = source.matrix_world.copy()
    if hasattr(obj, 'dagorprops'):
        from ..object_properties.codec import parse_properties
        obj.dagorprops['renderable:b'] = False
        obj.dagorprops['collidable:b'] = True
        for key, value in parse_properties(properties).items():
            obj.dagorprops[key] = value
    return obj


def transfer_normals(context, source, target, strength=1.0, keep_material=''):
    mask = re.compile(keep_material) if keep_material else None
    source_mesh = evaluated_mesh(context, source)
    try:
        source_mesh.calc_loop_triangles()
        triangles = list(source_mesh.loop_triangles)
        if not triangles:
            raise ValueError(f'{source.name}: no triangles for normal transfer')
        tree = BVHTree.FromPolygons([vert.co for vert in source_mesh.vertices],
                                   [triangle.vertices for triangle in triangles], all_triangles=True)
        target_mesh = target.data
        target_to_source = source.matrix_world.inverted() @ target.matrix_world
        normal_to_target = target_to_source.transposed().to_3x3()
        normals = [normal.vector.copy() for normal in target_mesh.corner_normals]
        for polygon in target_mesh.polygons:
            material = target_mesh.materials[polygon.material_index] if polygon.material_index < len(target_mesh.materials) else None
            if mask is not None and material is not None and mask.search(material.name):
                continue
            for loop_index in polygon.loop_indices:
                point = target_mesh.vertices[target_mesh.loops[loop_index].vertex_index].co
                nearest, _, triangle_index, _ = tree.find_nearest(target_to_source @ point)
                if triangle_index is None:
                    continue
                triangle = triangles[triangle_index]
                positions = [source_mesh.vertices[index].co for index in triangle.vertices]
                values = [source_mesh.corner_normals[index].vector for index in triangle.loops]
                normal = normal_to_target @ barycentric_transform(nearest, *positions, *values)
                normal.normalize()
                normals[loop_index] = normals[loop_index].lerp(normal, strength).normalized()
        target_mesh.normals_split_custom_set(normals)
        target_mesh.update()
    finally:
        bpy.data.meshes.remove(source_mesh)


def puff_normals(obj, strength=1.0, center_height=0.0, keep_material=''):
    mesh = obj.data
    if not mesh.vertices:
        return
    minimum = Vector(tuple(min(vert.co[axis] for vert in mesh.vertices) for axis in range(3)))
    maximum = Vector(tuple(max(vert.co[axis] for vert in mesh.vertices) for axis in range(3)))
    center = (minimum + maximum) * 0.5
    center.z = minimum.z + center_height
    mask = re.compile(keep_material) if keep_material else None
    excluded = set()
    if mask is not None:
        for polygon in mesh.polygons:
            material = mesh.materials[polygon.material_index] if polygon.material_index < len(mesh.materials) else None
            if material is not None and mask.search(material.name):
                excluded.update(polygon.loop_indices)
    normals = []
    for index, (loop, original) in enumerate(zip(mesh.loops, mesh.corner_normals)):
        direction = mesh.vertices[loop.vertex_index].co - center
        normal = original.vector.copy()
        if direction.length_squared and index not in excluded:
            normal = normal.lerp(direction.normalized(), strength).normalized()
        normals.append(normal)
    mesh.normals_split_custom_set(normals)
    mesh.update()


def volume_normals(context, target, voxel_size, strength, keep_material,
                   keep_volume=False, surface_size=0, tension=0.5):
    mesh = evaluated_mesh(context, target)
    volume = bpy.data.objects.new('Dagor temporary normal volume', mesh)
    context.scene.collection.objects.link(volume)
    volume.matrix_world = target.matrix_world.copy()
    success = False
    try:
        if surface_size > 0:
            solidify = volume.modifiers.new('Polysurface thickness', 'SOLIDIFY')
            solidify.thickness = surface_size * max(tension, 0.01) * 2
            solidify.offset = 0
        remesh = volume.modifiers.new('Normal volume', 'REMESH')
        remesh.mode = 'VOXEL'
        remesh.voxel_size = voxel_size
        remesh.use_smooth_shade = True
        smooth = volume.modifiers.new('Smooth normal volume', 'SMOOTH')
        smooth.iterations = min(50, max(5, round(surface_size / voxel_size)))
        transfer_normals(context, volume, target, strength, keep_material)
        success = True
        if keep_volume:
            volume.name = target.name + '_normal_volume'
            volume.hide_set(True)
            if hasattr(volume, 'dagorprops'):
                volume.dagorprops['renderable:b'] = False
                volume.dagorprops['cast_shadows:b'] = False
        return volume if keep_volume else None
    finally:
        if not keep_volume or not success:
            bpy.data.objects.remove(volume, do_unlink=True)
            bpy.data.meshes.remove(mesh)


class DAGOR_OT_Generate_LODs(bpy.types.Operator):
    bl_idname = 'dt.generate_lods'
    bl_label = 'Generate LODs and Collisions'
    bl_options = {'REGISTER', 'UNDO'}
    count: IntProperty(name='Additional LODs', default=3, min=0, max=20)
    ratio: FloatProperty(name='Reduction ratio per LOD', default=0.5, min=0.01, max=1)
    collision: BoolProperty(name='Generate convex collision', default=False)
    keep_materials: StringProperty(name='Keep collision materials', description='Comma-separated names or wildcard patterns')
    remove_materials: StringProperty(name='Exclude collision materials', description='Comma-separated names or wildcard patterns')
    use_cut_height: BoolProperty(name='Cut collision at local height', default=False)
    cut_height: FloatProperty(name='Collision cut height', default=1)
    collision_properties: StringProperty(name='Collision properties', description='Typed properties separated by semicolons')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        sources = selected_meshes(context)
        memberships = {source: list(source.users_collection) for source in sources}
        objects, meshes, collections = set(bpy.data.objects), set(bpy.data.meshes), set(bpy.data.collections)
        try:
            for source in sources:
                generate_lods(context, source, self.count, self.ratio)
                if self.collision:
                    generate_collision(context, source, self.keep_materials, self.remove_materials,
                                       self.cut_height if self.use_cut_height else None, self.collision_properties)
        except (ValueError, RuntimeError) as error:
            for source, previous in memberships.items():
                for collection in previous:
                    if source.name not in collection.objects:
                        collection.objects.link(source)
            for obj in set(bpy.data.objects) - objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            for collection in set(bpy.data.collections) - collections:
                bpy.data.collections.remove(collection)
            for mesh in set(bpy.data.meshes) - meshes:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class DAGOR_OT_Vegetation_Normals(bpy.types.Operator):
    bl_idname = 'dt.vegetation_normals'
    bl_label = 'Vegetation Normals'
    bl_options = {'REGISTER', 'UNDO'}
    mode: EnumProperty(items=[('TRANSFER', 'Transfer from Active', 'Transfer interpolated surface normals'),
                              ('PUFF', 'Puffiness', 'Blend normals away from a ground-centered origin'),
                              ('POLYSURFACE', 'Polysurface', 'Build a thickened voxel surface for foliage normals'),
                              ('VOLUME', 'Volume', 'Voxelize and smooth a normal-transfer volume')])
    strength: FloatProperty(name='Strength', default=1, min=0, max=1)
    center_height: FloatProperty(name='Center height', default=0)
    voxel_size: FloatProperty(name='Volume voxel size', default=0.1, min=0.001)
    keep_material: StringProperty(name='Keep normals on material')
    keep_volume: BoolProperty(name='Keep generated normal volume', default=False)
    surface_size: FloatProperty(name='Polysurface size', default=0.2, min=0.001)
    tension: FloatProperty(name='Polysurface tension', default=0.5, min=0, max=1)

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        self.layout.prop(self, 'mode')
        self.layout.prop(self, 'strength')
        if self.mode == 'PUFF':
            self.layout.prop(self, 'center_height')
        self.layout.prop(self, 'keep_material')
        if self.mode in {'VOLUME', 'POLYSURFACE'}:
            self.layout.prop(self, 'voxel_size')
            self.layout.prop(self, 'keep_volume')
        if self.mode == 'POLYSURFACE':
            self.layout.prop(self, 'surface_size')
            self.layout.prop(self, 'tension')

    def execute(self, context):
        targets = selected_meshes(context)
        source = context.active_object
        if self.mode == 'TRANSFER':
            if source not in targets or len(targets) < 2:
                self.report({'ERROR'}, 'Select target meshes and make the source mesh active')
                return {'CANCELLED'}
            targets.remove(source)
        try:
            if self.keep_material:
                re.compile(self.keep_material)
            for target in targets:
                # Keep edits on selected objects when mesh data is instanced.
                if target.data.users > 1:
                    target.data = target.data.copy()
                if self.mode == 'PUFF':
                    puff_normals(target, self.strength, self.center_height, self.keep_material)
                elif self.mode in {'VOLUME', 'POLYSURFACE'}:
                    volume_normals(context, target, self.voxel_size, self.strength, self.keep_material,
                                   self.keep_volume, self.surface_size if self.mode == 'POLYSURFACE' else 0,
                                   self.tension)
                else:
                    transfer_normals(context, source, target, self.strength, self.keep_material)
        except (ValueError, RuntimeError, re.error) as error:
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class DAGOR_OT_Clean_Asset_Names(bpy.types.Operator):
    bl_idname = 'dt.clean_asset_names'
    bl_label = 'Fix Illegal Asset Names'
    bl_description = 'Replace unsupported characters in selected object names with underscores'
    bl_options = {'REGISTER', 'UNDO'}
    illegal: StringProperty(name='Illegal characters', default=' <>:"/\\|?*')
    replacement: StringProperty(name='Replace with', default='_')
    transliterate: BoolProperty(name='Latinize Russian characters', default=True)
    ascii_only: BoolProperty(name='ASCII names for DAG compatibility', default=True)
    lowercase: BoolProperty(name='Convert names to lowercase', default=False)
    objects: BoolProperty(name='Fix selected object names', default=True)
    collections: BoolProperty(name='Fix their collection names', default=False)
    materials: BoolProperty(name='Fix their material names', default=False)
    warn_textures: BoolProperty(name='Warn about texture names and paths', default=True)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        targets = set(context.selected_objects) if self.objects else set()
        if self.collections:
            targets.update(collection for obj in context.selected_objects for collection in obj.users_collection)
        materials = {slot.material for obj in context.selected_objects for slot in obj.material_slots if slot.material}
        if self.materials:
            targets.update(materials)
        collisions = []
        for target in targets:
            requested = clean_asset_name(target.name, self.illegal, self.replacement,
                                         self.transliterate, self.ascii_only, self.lowercase)
            target.name = requested
            if target.name != requested:
                collisions.append(target.name)
        texture_warnings = []
        if self.warn_textures:
            for material in materials:
                if not material.use_nodes:
                    continue
                for node in material.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        path = node.image.filepath
                        if any(character in self.illegal for character in node.image.name) or not node.image.name.isascii() or not path.isascii():
                            texture_warnings.append(path or node.image.name)
        if collisions or texture_warnings:
            from ..helpers.texts import log
            for name in collisions:
                log(f'Name collision resolved as {name}\n', type='WARNING')
            for path in texture_warnings:
                log(f'Texture name/path needs review: {path}\n', type='WARNING')
            self.report({'WARNING'}, f'{len(collisions)} naming conflicts; {len(texture_warnings)} texture warnings in the Dagor log')
        return {'FINISHED'}


def clean_asset_name(name, illegal=' <>:"/\\|?*', replacement='_', transliterate=True,
                     ascii_only=True, lowercase=False):
    russian = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    latin = ('a', 'b', 'v', 'g', 'd', 'e', 'yo', 'zh', 'z', 'i', 'y', 'k', 'l', 'm',
             'n', 'o', 'p', 'r', 's', 't', 'u', 'f', 'kh', 'ts', 'ch', 'sh', 'shch', '', 'y', '', 'e', 'yu', 'ya')
    table = dict(zip(russian, latin))
    output = []
    for character in name:
        lower = character.lower()
        if transliterate and lower in table:
            value = table[lower]
            output.append(value.capitalize() if character.isupper() else value)
        elif character in illegal or ord(character) < 32 or (ascii_only and not character.isascii()):
            output.append(replacement)
        else:
            output.append(character)
    result = ''.join(output).strip(' .') or 'asset'
    if result.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}:
        result = '_' + result
    return result.lower() if lowercase else result


class DAGOR_PT_Asset_Authoring(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Asset Authoring'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator('dt.generate_lods')
        for mode, label in [('TRANSFER', 'Transfer Normals'), ('PUFF', 'Puffiness Normals'),
                             ('POLYSURFACE', 'Polysurface Normals'),
                             ('VOLUME', 'Volume Normals')]:
            self.layout.operator('dt.vegetation_normals', text=label).mode = mode
        self.layout.operator('dt.clean_asset_names')


classes = (DAGOR_OT_Generate_LODs, DAGOR_OT_Vegetation_Normals,
           DAGOR_OT_Clean_Asset_Names, DAGOR_PT_Asset_Authoring)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
