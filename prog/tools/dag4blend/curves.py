"""Evaluate NURBS centerlines through Blender's own curve tessellator."""
from types import SimpleNamespace

import bpy
from mathutils import Vector


def evaluated_polylines(obj):
    temporary = obj.copy()
    data = obj.data.copy()
    temporary.data = data
    bpy.context.scene.collection.objects.link(temporary)
    data.dimensions = '3D'
    data.bevel_depth = 0
    data.bevel_object = None
    data.extrude = 0
    mesh = None
    try:
        depsgraph = bpy.context.evaluated_depsgraph_get()
        evaluated = temporary.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        if mesh.polygons:
            raise ValueError(f'{obj.name}: curve modifiers produce a surface; export it as a mesh')
        neighbors = {vertex.index: [] for vertex in mesh.vertices}
        for edge in mesh.edges:
            a, b = edge.vertices
            neighbors[a].append(b)
            neighbors[b].append(a)
        if any(len(links) > 2 for links in neighbors.values()):
            raise ValueError(f'{obj.name}: evaluated spline has branching edges')
        remaining = set(neighbors)
        splines = []
        while remaining:
            seed = min(remaining)
            component, queue = set(), [seed]
            while queue:
                index = queue.pop()
                if index in component:
                    continue
                component.add(index)
                queue.extend(neighbors[index])
            endpoints = [index for index in component if len(neighbors[index]) < 2]
            closed = not endpoints
            index = min(endpoints or component)
            previous, ordered, visited = None, [], set()
            while index not in visited:
                ordered.append(index)
                visited.add(index)
                following = [neighbor for neighbor in neighbors[index] if neighbor != previous]
                if not following:
                    break
                previous, index = index, following[0]
            points = [SimpleNamespace(co=Vector((*mesh.vertices[index].co, 1))) for index in ordered]
            splines.append(SimpleNamespace(type='POLY', points=points,
                                            use_cyclic_u=closed, use_cyclic_v=False))
            remaining.difference_update(component)
        return SimpleNamespace(splines=splines)
    finally:
        if mesh is not None:
            evaluated.to_mesh_clear()
        bpy.data.objects.remove(temporary, do_unlink=True)
        if data.users == 0:
            bpy.data.curves.remove(data)
