"""Damage chunks and engine primitive/convex collision authoring."""
import hashlib
import random

import bmesh
import bpy
from bpy.props import BoolProperty, EnumProperty, FloatProperty, FloatVectorProperty, IntProperty, StringProperty
from mathutils import Euler, Matrix, Vector

from .authoring import evaluated_mesh, selected_meshes
from ..object_properties.codec import parse_properties


def hull_from_points(points):
    bm = bmesh.new()
    try:
        for point in points:
            bm.verts.new(point)
        result = bmesh.ops.convex_hull(bm, input=list(bm.verts))
    except Exception:
        bm.free()
        raise
    unused = [element for element in result['geom_interior'] + result['geom_unused']
              if isinstance(element, bmesh.types.BMVert) and element.is_valid]
    if unused:
        bmesh.ops.delete(bm, geom=list(set(unused)), context='VERTS')
    bm.normal_update()
    return bm


def bounded_convex(points, maximum, offset):
    # Farthest-point sampling limits hull complexity. Expanding each resulting
    # supporting plane conservatively ensures omitted source points remain inside.
    sampled = [points[0]]
    nearest = [(point - points[0]).length_squared for point in points]
    for _ in range(min(maximum, len(points)) - 1):
        index = max(range(len(points)), key=nearest.__getitem__)
        if nearest[index] < 1e-16:
            break
        sampled.append(points[index])
        nearest = [min(distance, (point - points[index]).length_squared)
                   for point, distance in zip(points, nearest)]
    bm = hull_from_points(sampled)
    if not bm.faces or bm.calc_volume() <= 1e-12:
        bm.free()
        low = Vector(tuple(min(point[axis] for point in points) for axis in range(3)))
        high = Vector(tuple(max(point[axis] for point in points) for axis in range(3)))
        bm = hull_from_points([Vector((x, y, z)) for x in (low.x, high.x)
                               for y in (low.y, high.y) for z in (low.z, high.z)])
    if bm.calc_volume() <= 1e-12:
        bm.free()
        raise ValueError('Convex collision requires non-coplanar geometry')
    center = sum((vertex.co for vertex in bm.verts), Vector()) / len(bm.verts)
    factor = 1.0
    for face in bm.faces:
        distance = face.normal.dot(face.verts[0].co - center)
        if distance > 1e-12:
            required = max(face.normal.dot(point - center) for point in points) + offset
            factor = max(factor, required / distance)
    for vertex in bm.verts:
        vertex.co = center + (vertex.co - center) * factor
    return bm


def damage_collider(context, source, shape='BOX', maximum=32, offset=0,
                    rotation_limits=(0, 0, 0), seed=0, postfix='_cls'):
    evaluated = evaluated_mesh(context, source)
    try:
        points = [vertex.co.copy() for vertex in evaluated.vertices]
    finally:
        bpy.data.meshes.remove(evaluated)
    if not points:
        raise ValueError(f'{source.name}: no geometry for collision generation')
    digest = int.from_bytes(hashlib.blake2s(source.name.encode('utf8')).digest()[:4], 'little')
    rng = random.Random(seed ^ digest)
    rotation = Euler(tuple(rng.uniform(-limit, limit) for limit in rotation_limits)).to_matrix().to_4x4()
    inverse = rotation.inverted()
    rotated = [inverse @ point for point in points]
    low = Vector(tuple(min(point[axis] for point in rotated) for axis in range(3)))
    high = Vector(tuple(max(point[axis] for point in rotated) for axis in range(3)))
    center = (low + high) / 2
    if shape == 'CONVEX':
        bm = bounded_convex(rotated, maximum, offset)
        for vertex in bm.verts:
            vertex.co -= center
    else:
        # The public physObj exporter fits all three primitives from localBox.
        # Bounding meshes preserve those exact native fitter inputs.
        half = (high - low) / 2 + Vector((offset, offset, offset))
        if min(half) <= 0:
            raise ValueError(f'{source.name}: collision dimensions must be positive')
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=2)
        for vertex in bm.verts:
            vertex.co = Vector(tuple(vertex.co[axis] * half[axis] for axis in range(3)))
    mesh = bpy.data.meshes.new(source.name + postfix)
    try:
        bm.to_mesh(mesh)
    finally:
        bm.free()
    collider = bpy.data.objects.new(mesh.name, mesh)
    collection = source.users_collection[0] if source.users_collection else context.scene.collection
    collection.objects.link(collider)
    collider.parent = source
    collider.matrix_world = source.matrix_world @ rotation @ Matrix.Translation(center)
    collider.display_type = 'WIRE' if shape == 'CONVEX' else 'BOUNDS'
    if shape != 'CONVEX':
        collider.display_bounds_type = shape
    collider.dagorprops['renderable:b'] = False
    collider.dagorprops['cast_shadows:b'] = False
    collider.dagorprops['collidable:b'] = True
    collider.dagorprops['collision:t'] = shape.lower()
    # Public physObj supports box/sphere/capsule. Convex data is authored for
    # the collision-resource exporter, which consumes collision:t="convex".
    collider.dagorprops['collType:t'] = shape.lower() if shape != 'CONVEX' else 'none'
    collider.dagorprops['massType:t'] = 'sphere' if shape == 'SPHERE' else ('mesh' if shape == 'CONVEX' else 'box')
    return collider


def set_properties(obj, values, preserve):
    if not preserve:
        for key in list(obj.dagorprops.keys()):
            del obj.dagorprops[key]
    for key, value in values.items():
        obj.dagorprops[key] = value


class DAGOR_OT_Setup_Damage(bpy.types.Operator):
    bl_idname = 'dt.setup_damage'
    bl_label = 'Damage Chunk Setup'
    bl_options = {'REGISTER', 'UNDO'}
    shape: EnumProperty(name='Collision type', items=[('BOX', 'Box', 'Native physObj box fitter'),
        ('SPHERE', 'Sphere', 'Native physObj sphere fitter'), ('CAPSULE', 'Capsule', 'Native physObj capsule fitter'),
        ('CONVEX', 'Convex Collision Asset', 'Convex geometry for a collision resource')])
    visible_properties: StringProperty(name='Visible chunk properties',
        default='animated_node:b=yes; physObj:b=yes; collidable:b=no; massType:t="none"')
    collision_properties: StringProperty(name='Collision properties', default='density:r=100; phmat:t=""')
    preserve: BoolProperty(name='Preserve old user properties', default=True)
    maximum: IntProperty(name='Maximum convex vertices', default=32, min=8, max=256)
    offset: FloatProperty(name='Collision surface offset', default=0, min=0)
    rotation_limits: FloatVectorProperty(name='Random rotation limits', subtype='EULER', size=3, default=(0, 0, 0), min=0)
    seed: IntProperty(name='Random seed', default=0)
    postfix: StringProperty(name='Collision name postfix', default='_cls')

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT' and bool(selected_meshes(context))

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

    def execute(self, context):
        sources = selected_meshes(context)
        previous = {obj: dict(obj.dagorprops.items()) for obj in sources}
        objects, meshes = set(bpy.data.objects), set(bpy.data.meshes)
        try:
            visible = parse_properties(self.visible_properties)
            collision = parse_properties(self.collision_properties)
            if 'broken_properties:t' in visible or 'broken_properties:t' in collision:
                raise ValueError('Correct invalid typed properties before creating damage chunks')
            for source in sources:
                collider = damage_collider(context, source, self.shape, self.maximum, self.offset,
                                           self.rotation_limits, self.seed, self.postfix)
                set_properties(source, visible, self.preserve)
                set_properties(collider, collision, True)
        except (ValueError, RuntimeError) as error:
            for source, values in previous.items():
                set_properties(source, values, False)
            for obj in set(bpy.data.objects) - objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            for mesh in set(bpy.data.meshes) - meshes:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        return {'FINISHED'}


class DAGOR_PT_Damage_Setup(bpy.types.Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Dagor'
    bl_context = 'objectmode'
    bl_label = 'Damage Setup'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        self.layout.operator('dt.setup_damage')


classes = (DAGOR_OT_Setup_Damage, DAGOR_PT_Damage_Setup)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
