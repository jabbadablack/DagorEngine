"""DAG skin weights: packed ushort IDs, 4x3 bind matrices and bone-major floats."""
import struct
from mathutils import Matrix


def stored_matrix(values):
    if len(values) != 16:
        raise ValueError('Stored bone bind matrix requires sixteen components')
    return Matrix([values[index:index + 4] for index in range(0, 16, 4)])


def effective_bind(bone):
    raw, baseline = bone.get('dagor_bind_matrix'), bone.get('dagor_edit_bind_matrix')
    if raw is None or baseline is None:
        return bone.matrix_local.copy()
    # Preserve the original affine bind while honoring subsequent rest edits.
    return bone.matrix_local @ stored_matrix(baseline).inverted() @ stored_matrix(raw)


def native_pose_matrix(pose_bone):
    bone = pose_bone.bone
    if bone.get('dagor_bind_matrix') is None:
        return pose_bone.matrix.copy()
    return pose_bone.matrix @ bone.matrix_local.inverted() @ effective_bind(bone)


def write_skin(writer, bones, vertex_count, weights):
    if len(bones) != len(weights) or any(len(row) != vertex_count for row in weights):
        raise ValueError('Skin weight dimensions do not match the exported mesh')
    writer.writeUShort(len(bones))
    for node_id, matrix in bones:
        writer.writeUShort(node_id)
        writer.writeMatrix4x3(matrix)
    writer.writeDWord(vertex_count)
    for row in weights:
        writer.file.write(struct.pack(f'<{vertex_count}f', *row))


def collect_skin(obj, armature, bone_ids, origin_inverse=None):
    bones, rows = [], []
    # Use vertex groups after export preparation: topology-changing modifiers
    # and cleanup must not leave a weight matrix indexed by the original mesh.
    memberships = [dict((group.group, group.weight) for group in vert.groups)
                   for vert in obj.data.vertices]
    for bone in armature.data.bones:
        group = obj.vertex_groups.get(bone.name)
        if group is None:
            continue
        weights = [members.get(group.index, 0.0) for members in memberships]
        if not any(weights):
            continue
        node_id = bone_ids.get((armature, bone.name))
        if node_id is None:
            raise ValueError(f'{obj.name}: skin references missing bone {bone.name}')
        matrix = armature.matrix_world @ effective_bind(bone)
        if origin_inverse is not None:
            matrix = origin_inverse @ matrix
        matrix[1], matrix[2] = matrix[2].copy(), matrix[1].copy()
        bones.append((node_id, matrix.transposed()))
        rows.append(weights)
    if not bones:
        return None
    # Normalize influences just as Blender's armature deform does by default.
    for index in range(len(obj.data.vertices)):
        total = sum(row[index] for row in rows)
        if total <= 0:
            continue
        for row in rows:
            row[index] /= total
    return bones, rows


def read_skin(payload):
    if len(payload) < 2:
        raise ValueError('Truncated DAG skin bone count')
    count, = struct.unpack_from('<H', payload)
    if count == 0:
        return None
    offset = 2 + 50 * count
    if len(payload) < offset + 4:
        raise ValueError('Truncated DAG skin bind matrices')
    vertex_count, = struct.unpack_from('<I', payload, offset)
    offset += 4
    if len(payload) != offset + count * vertex_count * 4:
        raise ValueError('DAG skin weight dimensions exceed the chunk size')
    bones = []
    for index in range(count):
        node_id, *values = struct.unpack_from('<H12f', payload, 2 + index * 50)
        matrix = Matrix.Identity(4)
        for row in range(4):
            for column in range(3):
                matrix[row][column] = values[row * 3 + column]
        bones.append((node_id, matrix))
    weights = [list(struct.unpack_from(f'<{vertex_count}f', payload, offset + index * vertex_count * 4))
               for index in range(count)]
    if any(not (0 <= value <= 1) for row in weights for value in row):
        raise ValueError('DAG skin weights must be finite values between zero and one')
    return bones, weights


def restore_skins(context, collection, root):
    """Replace imported skeleton helpers with Blender bones and armature modifiers."""
    import bpy
    from .object_properties.codec import parse_properties

    nodes = {}

    def visit(node):
        nodes[node.id] = node
        for child in node.children:
            visit(child)

    visit(root)
    objects = {obj['_dag_node_id']: obj for obj in collection.objects if '_dag_node_id' in obj}
    skinned = [node for node in nodes.values() if node.skin is not None]
    if not skinned:
        return
    binds = {}
    bone_ids = {node.id for node in nodes.values() if parse_properties(node.objProps).get('dagor_bone:b', False)}
    marked_bones = bool(bone_ids)
    for node in skinned:
        bones, weights = node.skin
        if len(objects[node.id].data.vertices) != len(weights[0]):
            raise ValueError(f'{node.name}: imported mesh vertex count does not match skin weights')
        for node_id, stored in bones:
            if node_id not in objects:
                raise ValueError(f'{node.name}: skin references missing node {node_id}')
            bone_ids.add(node_id)
            matrix = stored.transposed()
            matrix[1], matrix[2] = matrix[2].copy(), matrix[1].copy()
            if node_id in binds and any(abs(binds[node_id][i][j] - matrix[i][j]) > 1e-4
                                        for i in range(4) for j in range(4)):
                raise ValueError('Meshes contain conflicting bind poses for the same bone')
            binds[node_id] = matrix
    reverse_objects = {obj: node_id for node_id, obj in objects.items()}
    if not marked_bones:
        # Classic Max files identify weighted bones by ID, without a Blender
        # marker. Retain unweighted helper ancestors in their skeleton too.
        for node_id in list(bone_ids):
            parent = objects[node_id].parent
            while parent is not None and parent.type == 'EMPTY' and parent in reverse_objects:
                bone_ids.add(reverse_objects[parent])
                parent = parent.parent
        roots = [node_id for node_id in bone_ids if reverse_objects.get(objects[node_id].parent) not in bone_ids]
        if len(roots) == 1 and roots[0] not in binds:
            bone_ids.remove(roots[0])
    names = [nodes[node_id].name for node_id in bone_ids]
    if len(names) != len(set(names)):
        raise ValueError('DAG skeleton contains duplicate bone names')
    bone_objects = {objects[node_id] for node_id in bone_ids}
    root_parents = {obj.parent for obj in bone_objects if obj.parent not in bone_objects}
    root_helper = next(iter(root_parents)) if len(root_parents) == 1 else None
    if root_helper is not None and root_helper.type != 'EMPTY':
        root_helper = None
    name = root_helper.name if root_helper else collection.name + '_skeleton'
    world = root_helper.matrix_world.copy() if root_helper else Matrix.Identity(4)
    armature = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name + '_import', armature)
    collection.objects.link(rig)
    context.view_layer.update()
    rig.parent = root_helper.parent if root_helper else None
    rig.matrix_world = world
    inverse = world.inverted()
    selected = [obj.name for obj in context.selected_objects]
    active = context.view_layer.objects.active
    active_name = active.name if active else None
    try:
        bpy.ops.object.select_all(action='DESELECT')
        rig.select_set(True)
        context.view_layer.objects.active = rig
        with context.temp_override(object=rig, active_object=rig,
                                   selected_objects=[rig], selected_editable_objects=[rig]):
            bpy.ops.object.mode_set(mode='EDIT')
        edit = {}
        for node_id in sorted(bone_ids):
            bone = armature.edit_bones.new(nodes[node_id].name)
            bone.head = (0, 0, 0)
            bone.tail = (0, 0.1, 0)
            bone.matrix = inverse @ binds.get(node_id, objects[node_id].matrix_world)
            edit[node_id] = bone
        for node_id, bone in edit.items():
            parent_id = reverse_objects.get(objects[node_id].parent)
            if parent_id in edit:
                bone.parent = edit[parent_id]
        with context.temp_override(object=rig, active_object=rig):
            bpy.ops.object.mode_set(mode='OBJECT')
        for node_id in bone_ids:
            bone = armature.bones[nodes[node_id].name]
            raw_bind = inverse @ binds.get(node_id, objects[node_id].matrix_world)
            bone['dagor_bind_matrix'] = [value for row in raw_bind for value in row]
            bone['dagor_edit_bind_matrix'] = [value for row in bone.matrix_local for value in row]
            bone['dagor_script'] = nodes[node_id].objProps
        for node in skinned:
            target = objects[node.id]
            bones, rows = node.skin
            for (node_id, _), weights in zip(bones, rows):
                group = target.vertex_groups.new(name=nodes[node_id].name)
                for index, weight in enumerate(weights):
                    if weight > 0:
                        group.add([index], weight, 'REPLACE')
            modifier = target.modifiers.new('Dagor skin', 'ARMATURE')
            modifier.object = rig
        for obj in list(collection.objects):
            if obj in bone_objects or obj == root_helper:
                continue
            if obj.parent in bone_objects or (root_helper is not None and obj.parent == root_helper):
                transform = obj.matrix_world.copy()
                bone_name = nodes[reverse_objects[obj.parent]].name if obj.parent in bone_objects else None
                obj.parent = rig
                if bone_name is not None:
                    obj.parent_type = 'BONE'
                    obj.parent_bone = bone_name
                obj.matrix_world = transform
        geometry = [(obj, obj.matrix_world.copy()) for obj in bone_objects if obj.type != 'EMPTY']
        for obj, transform in geometry:
            node_id = reverse_objects[obj]
            obj.name = nodes[node_id].name + '_geometry'
            obj.parent = rig
            if nodes[node_id].skin is None:
                obj.parent_type = 'BONE'
                obj.parent_bone = nodes[node_id].name
            else:
                obj.parent_type = 'OBJECT'
            obj.matrix_world = transform
            if hasattr(obj, 'dagorprops'):
                for key in ('physObj:b', 'animated_node:b', 'dagor_bone:b'):
                    if key in obj.dagorprops:
                        del obj.dagorprops[key]
        for obj in bone_objects:
            if obj.type == 'EMPTY':
                bpy.data.objects.remove(obj, do_unlink=True)
        if root_helper:
            bpy.data.objects.remove(root_helper, do_unlink=True)
        rig.name = name
    finally:
        if rig.mode != 'OBJECT':
            with context.temp_override(object=rig, active_object=rig):
                bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        for name in selected:
            obj = context.view_layer.objects.get(name)
            if obj is not None:
                obj.select_set(True)
        active = context.view_layer.objects.get(active_name) if active_name else None
        if active is not None:
            context.view_layer.objects.active = active
        else:
            context.view_layer.objects.active = rig
