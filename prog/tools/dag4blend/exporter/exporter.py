import mathutils
import re

from os         import makedirs, replace, unlink
from os.path    import exists, join, dirname, abspath
from tempfile   import NamedTemporaryFile

import bpy
from bpy.path                       import ensure_ext
from mathutils                      import Matrix
from shutil                         import copyfile
from bpy_extras.io_utils            import ExportHelper
from bpy.props                      import StringProperty, BoolProperty, EnumProperty, PointerProperty
from bpy.types                      import Operator
from ..object_properties            import object_properties
from ..object_properties.codec      import parse_properties, serialize_properties, as_bool
from .                              import writer
from ..dagMath                      import mul
from ..constants                    import *
from ..face                         import FaceExp
from ..node                         import NodeExp
from ..lights                       import DagLight
from ..skin                         import collect_skin, write_skin, effective_bind, native_pose_matrix
from ..mapping                      import write_mesh_data
from ..curves                       import evaluated_polylines
from ..nodeMaterial                 import MaterialExp
from ..mesh                         import MeshExp
from ..popup.popup_functions    import show_popup
from ..helpers.names                import ensure_no_path
from ..helpers.multiline            import _label_multiline
from ..helpers.texts                import log
from ..helpers.version              import get_blender_version
from ..tools.tools_panel            import apply_modifiers, fix_mat_slots, optimize_mat_slots, preserve_sharp
from ..tools.tools_functions        import *
from ..dagormat.rw_dagormat_text    import dagormat_prop_to_string

from ..smooth_groups.smooth_groups              import int_to_uint
from ..smooth_groups.mesh_calc_smooth_groups    import objects_calc_smooth_groups


SUPPORTED_TYPES = ('MESH', 'CURVE', 'EMPTY', 'LIGHT', 'ARMATURE', 'CAMERA')


def legacy_variation_suffix(name):
    match = re.fullmatch(r'(?:(DMG2|DMG|DESTR|EXPL)_)?LOD(\d\d)', name, re.IGNORECASE)
    if match and int(match.group(2)) < 16:
        prefix = '_' + match.group(1).lower() if match.group(1) else ''
        return f'{prefix}.lod{match.group(2)}.dag'
    return {'dm': '_dm.dag', 'xray': '_xray.dag', 'destr': '_destr.lod00.dag'}.get(name.casefold())

#reorders UVMap names to match three first chanels to viewport preview
def sort_uv_names(keys):
    keys.sort()
    sorted = []
    for name in ['UVMap', 'UVMap.001', 'UVMap.002']:
        if name in keys:
            sorted.append(name)
            keys.remove(name)
    sorted += keys
    return sorted

#CLASSES

class DAG_PT_export(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Mode:"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator is not None and operator.bl_idname == 'EXPORT_SCENE_OT_dag'

    def draw(self, context):
        l = self.layout
        l.use_property_decorate = False  # No animation.
        S = context.scene
        P = bpy.data.scenes[0].dag4blend.exporter
        sfile = context.space_data
        operator = sfile.active_operator
        hint='Wait... What mode we in?'
        types = l.box()
        types.label(text='Data Types')
        for name in ('meshes', 'helpers', 'lights', 'curves', 'cameras', 'export_materials'):
            types.prop(operator, name)
        for name in ('normals', 'modifiers', 'mopt', 'clean_geometry', 'include_hidden'):
            l.prop(operator, name)
        l.prop_search(operator, 'origin_name', bpy.data, 'objects')
        if operator.limits == 'Sel.Separated':
            for name in ('filename_prefix', 'filename_suffix', 'include_collisions', 'collision_prefix'):
                l.prop(operator, name)
        if operator.limits == 'Legacy':
            l.prop(operator, 'legacy_selected_only')
        l.prop(operator, "limits")
        if operator.limits=='Visible':
            hint = 'Export all visible objects of supported types as single .dag.'
        elif operator.limits == 'Legacy':
            hint = 'Export LOD00, DMG_LOD00, DESTR, DM and XRAY collections using the chosen asset filename.'
        elif operator.limits=='Sel.Joined':
            hint = 'Export all selected objects of supported types as single .dag.'
        elif operator.limits=='Sel.Separated':
            hint = 'Export all visible objects of supported types as separate .dag, named as objects itself. User defined name will be ignored.'
        elif operator.limits=='Col.Separated':
            if P.collection==None:
                if S.collection.children.__len__()==0:
                    hint = "No sub-collections in Scene Collection. Scene Collection.dag can't be exported"
                else:
                    hint = 'Export each collection without sub-collections in scene as separate .dags, named as collections itself. User defined name will be ignored.'
            elif P.collection.children.__len__()>0:
                hint = f'Export each sub-collection of {P.collection.name} without children as separate .dags, named as collections itself. User defined name will be ignored.'
            else:
                hint = f'Export {P.collection.name}.dag. User defined name will be ignored.'
            l.prop(P,"collection")
            l.prop(P,"orphans")
        elif operator.limits=='Col.Joined':
            if P.collection==None:
                if S.collection.children.__len__()==0:
                    hint = "Select collection for export. Scene Collection.dag can't be exported"
                else:
                    hint = f'Export {S.collection.name}.dag (including objects of sub-collections). User defined name will be ignored.'
            l.prop(P,"collection")
        info=l.box()
        _label_multiline(context=context, text=hint, parent=info)

class DagExporter(Operator, ExportHelper):
    bl_idname = "export_scene.dag"
    bl_label = "Export DAG"
    bl_options = {'REGISTER', 'UNDO'}

    nodes = None
    writer = None
    last_index = 0

    # ImportHelper mixin class uses this
    filename_ext = ".dag"
    filter_glob: StringProperty(default="*.dag", options={'HIDDEN'})
    meshes: BoolProperty(name='Meshes', default=True)
    helpers: BoolProperty(name='Helpers and armatures', default=True)
    lights: BoolProperty(name='Lights', default=True)
    curves: BoolProperty(name='Splines', default=True)
    cameras: BoolProperty(name='Camera helpers', default=True,
                         description='DAG has no camera payload; export camera node transforms as helpers')
    export_materials: BoolProperty(name='Materials', default=True,
                                   description='When disabled, write placeholder materials')
    include_hidden: BoolProperty(name='Include hidden', default=False)
    origin_name: StringProperty(name='Export origin object',
        description='Origin for joined and collection exports; separate objects use their own pivots')
    filename_prefix: StringProperty(name='Filename prefix')
    filename_suffix: StringProperty(name='Filename suffix')
    include_collisions: BoolProperty(name='Include matching collision objects', default=False)
    collision_prefix: StringProperty(name='Collision object prefix', default='Cls_')
    legacy_selected_only: BoolProperty(name='Selected objects in legacy layers', default=False)
    normals: BoolProperty(
            name="Preserve custom normals",
            description="Export custom normals when it exists",
            default=True)

    modifiers: BoolProperty(
            name="Apply modifiers",
            description="Preserve effects of modifiers (exported geometry only)",
            default=True)

    mopt: BoolProperty(
            name="Optimize materials",
            description="Merge material slots with similar materials, remove unused slots",
            default=True)

    clean_geometry: BoolProperty(
            name="Clean degenerate and loose geometry",
            description="Remove short edges, degenerate faces and unused vertices from the export copy",
            default=False)

    orphans: BoolProperty(
            name="Export orphans",
            description="Export objects not in the bottom of hierarchy as separate .dags",
            default=True,
            options={'HIDDEN'})

    limits: EnumProperty(
                #(identifier, name, description)

        items = [('Visible','Visible','Export everithing as one dag'),
             ('Legacy','Legacy LOD Layers','Export LOD00, DMG_LOD00, DESTR, DM and XRAY collections as named variations'),
             ('Sel.Joined','Sel.Joined','Selected objects as one dag'),
             ('Sel.Separated','Sel.Separated','Selected objects as separate dags'),
             ('Col.Separated','Col.Separated','Chosen collection and subcollections as separate .dags'),
             ('Col.Joined','Col.Joined','Objects of chosen collection and subcollections as one .dag')],
        name = "",
        options={'HIDDEN'},
        default = 'Visible')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.writer = writer.DagWriter()
        self.last_index = 0
        self.nodes = list()
        self.materials = {}
        self.textures = []

    def createRootNode(self):
        node = NodeExp()
        node.id = 65535
        node.parent_id = -1
        node.tm = Matrix()
        node.tm.identity()
        node.wtm = Matrix()
        node.wtm.identity()
        node.renderable = False
        self.nodes.append(node)
        return node

    def writeCurves(self, curve):
        objChunkPos = self.writer.beginChunk(DAG_NODE_OBJ)
        splineShunkPos = self.writer.beginChunk(DAG_OBJ_SPLINES)
        self.writer.writeDWord(len(curve.splines))
        for spline in curve.splines:
            closed = spline.use_cyclic_u or spline.use_cyclic_v
            self.writer.writeByte(closed)
            points = spline.bezier_points if spline.type == 'BEZIER' else spline.points
            count = len(points)
            self.writer.writeDWord(count)
            for index, point in enumerate(points):
                if spline.type == 'BEZIER':
                    co, left, right = point.co, point.handle_left, point.handle_right
                else:
                    co = point.co.to_3d()
                    previous = points[(index - 1) % count].co.to_3d() if index or closed else co
                    following = points[(index + 1) % count].co.to_3d() if index + 1 < count or closed else co
                    left, right = co.lerp(previous, 1 / 3), co.lerp(following, 1 / 3)
                self.writer.writeByte(DAG_SKNOT_BEZIER)
                for vector in (co, left, right):
                    for component in vector:
                        self.writer.writeFloat(component)
        self.writer.endChunk(splineShunkPos)
        self.writer.endChunk(objChunkPos)
        return

    def writeMesh(self, mesh, skin=None):
        objChunkPos = self.writer.beginChunk(DAG_NODE_OBJ)
        write_mesh_data(self.writer, mesh)

        faceFlagChunkPos = self.writer.beginChunk(DAG_OBJ_FACEFLG)
        for f in mesh.faces:
            if f.flg is not None:
                self.writer.writeByte(f.flg)
            else:
                self.writer.writeByte(0)
        self.writer.endChunk(faceFlagChunkPos)

        if len(mesh.normals_ver) > 0:
            normalsChunkPos = self.writer.beginChunk(DAG_OBJ_NORMALS)
            self.writer.writeDWord(len(mesh.normals_ver))
            for n in mesh.normals_ver:
                self.writer.writeFloat(n[0])
                self.writer.writeFloat(n[1])
                self.writer.writeFloat(n[2])
            for f in mesh.normals_faces:
                self.writer.writeDWord(f[0])
                self.writer.writeDWord(f[2])
                self.writer.writeDWord(f[1])
            self.writer.endChunk(normalsChunkPos)

        if skin is not None:
            skin_pos = self.writer.beginChunk(DAG_OBJ_BONES)
            bones, weights = skin
            write_skin(self.writer, bones, len(mesh.vertices), weights)
            self.writer.endChunk(skin_pos)
        self.writer.endChunk(objChunkPos)

    def dumpCurve(self, o, node, scene):
        if o.type != 'CURVE':
            return
        if any(spline.type not in {'BEZIER', 'POLY'} for spline in o.data.splines):
            node.curves = evaluated_polylines(o)
            log(f'{o.name}: NURBS exported as evaluated polylines\n')
            return
        node.curves = o.data

    def gatherObjPropScript(self, obj, node):
        node.objFlg |= DAG_NF_RENDERABLE | DAG_NF_CASTSHADOW
        for key, flag in (('renderable:b', DAG_NF_RENDERABLE), ('cast_shadows:b', DAG_NF_CASTSHADOW)):
            try:
                if not as_bool(obj.dagorprops.get(key, True)):
                    node.objFlg &= ~flag
            except ValueError:
                log(f'{obj.name}: invalid boolean property {key}\n', type='ERROR')
        return serialize_properties(dict(obj.dagorprops.items()))
    def toMesh(self, o, scene):
        if o.type != 'MESH':
            try:
                me = o.to_mesh(scene, True, "PREVIEW")
            except Exception:
                me = None
        else:
            me = o.data
        return me

    def getEdgeKeys(self, o, scene):
        edge_keys = dict()
        me = self.toMesh(o, scene)
        if me is None:
            return edge_keys
        for p in me.polygons:
            for edge_key in p.edge_keys:
                edge_keys[edge_key] = edge_key
        return edge_keys

    def dumpMesh(self, obj, node, scene):
    #creating temporary object to keep originals untouched
        exp_obj=obj.copy()
        exp_obj.data=obj.data.copy()
        exp_obj['og_name']=obj.name
        me = exp_obj.data
        armatures = [modifier.object for modifier in exp_obj.modifiers
                     if modifier.type == 'ARMATURE' and modifier.show_viewport and modifier.object is not None]
        if len(armatures) > 1:
            raise ValueError(f'{obj.name}: multiple armature modifiers are not supported by DAG skinning')
        for modifier in list(exp_obj.modifiers):
            if modifier.type == 'ARMATURE':
                if modifier.show_viewport and (modifier.use_deform_preserve_volume or modifier.use_bone_envelopes or modifier.vertex_group):
                    raise ValueError(f'{obj.name}: disable preserve volume and bone envelopes for linear DAG skinning')
                exp_obj.modifiers.remove(modifier)
    #optional edits
        if self.modifiers:
            apply_modifiers(exp_obj)
        if self.mopt:
            fix_mat_slots(exp_obj)
            optimize_mat_slots(exp_obj)
    #mesh checks
        if not is_mesh_smooth(me):
            log(f'Node "{exp_obj["og_name"]}": flat shaded faces, exported without smooth group\n', type = 'WARNING')
        if is_mesh_empty(me):
            log(f'Node "{exp_obj["og_name"]}": no faces\n', type = 'WARNING')
        if self.clean_geometry:
            msg = mesh_verify_fix_degenerates(me)
            if msg is not None:
                log(f'Object "{exp_obj["og_name"]}": {msg}\n', type = 'WARNING')
            msg = mesh_verify_fix_loose(me)
            if msg is not None:
                log(f'Object "{exp_obj["og_name"]}": {msg}\n', type = 'WARNING')
    #necessary no matter what
        if get_blender_version()<4.1:
            preserve_sharp(exp_obj)
        fix_mat_slots(exp_obj)
        if not self.export_materials:
            exp_obj.data.materials.clear()
            from ..tools.tools_panel import get_autonamed
            exp_obj.data.materials.append(get_autonamed())
            for polygon in exp_obj.data.polygons:
                polygon.material_index = 0
        if exp_obj.data.attributes.get('SG') is None:
            objects_calc_smooth_groups([exp_obj])
    #collecting from pre-triangulated mesh to make it reversable on import
        edge_keys = self.getEdgeKeys(exp_obj, scene)
    #dag contains only triangles
        # Serialize Blender's tessellation directly. Applying triangulation or
        # passing through BMesh can discard overlapping native faces.

        node.objProps = self.gatherObjPropScript(exp_obj, node)
        node.materials_indices = [-1 for p in range(len(exp_obj.material_slots))]
        for i, slot in enumerate(exp_obj.material_slots):
            if slot.material.name not in self.materials:
                mat_exp = MaterialExp()
                mat_exp.index = len(self.materials)
                mat_exp.mat = slot.material
                self.materials[slot.material.name] = mat_exp

            val = self.materials.get(slot.material.name)
            if val is not None:
                node.materials_indices[i] = val.index
            else:
                node.materials_indices[i] = -1

        meshExp = MeshExp()

        me.calc_loop_triangles()
        from types import SimpleNamespace
        triangles = [SimpleNamespace(vertices=tuple(tri.vertices), loop_indices=tuple(tri.loops),
            index=tri.polygon_index, material_index=tri.material_index,
            edge_keys=tuple(tuple(sorted((tri.vertices[i], tri.vertices[(i + 1) % 3])))
                            for i in range(3))) for tri in me.loop_triangles]
        if get_blender_version()<4.1:
            me.calc_normals_split()

        for v in me.vertices:
            meshExp.vertices.append(v.co)
            meshExp.normals.append(-v.normal)

        smooth_groups=[]
        for sg in me.attributes['SG'].data:
            smooth_groups.append(int_to_uint(sg.value))

        for tri in triangles:
            face = FaceExp()
            face.f.append(tri.vertices[0])
            face.f.append(tri.vertices[2])
            face.f.append(tri.vertices[1])
            face.smgr = smooth_groups[tri.index]
            face.mat = tri.material_index
            for i, tri_edge in enumerate(tri.edge_keys):
                if tri_edge in edge_keys:
                    if i == 0:
                        face.flg =face.flg | DAG_FACEFLG_EDGE2 if face.flg is not None else DAG_FACEFLG_EDGE2
                    elif i == 1:
                        face.flg =face.flg | DAG_FACEFLG_EDGE1 if face.flg is not None else DAG_FACEFLG_EDGE1
                    elif i == 2:
                        face.flg =face.flg | DAG_FACEFLG_EDGE0 if face.flg is not None else DAG_FACEFLG_EDGE0
            meshExp.faces.append(face)
#Custom Normals
        for tri in me.loop_triangles:
            if self.normals and me.has_custom_normals:
                norm = [me.corner_normals[index].vector.copy() if get_blender_version() >= 4.1
                        else me.loops[index].normal.copy() for index in tri.loops]

                norm_face_ind = []
                for nv in norm:
                    norm_face_ind.append(meshExp.addNormal(nv))
                meshExp.normals_faces.append(norm_face_ind)
#UVMaps
        meshExp.uv = [dict() for p in range(NUMMESHTCH)]
        meshExp.uv_poly = [list() for p in range(NUMMESHTCH)]
        uv_amount = me.uv_layers.__len__()
        if uv_amount == 0:
            msg = f'Node "{exp_obj["og_name"]}" has no UVs\n'
            log(msg)
        elif uv_amount > 3:
            msg = f'Node "{exp_obj["og_name"]}" has {uv_amount} UV layers! Are you sure all of them are necessary?\n'
            log(msg, type = 'WARNING')
        uv_index = 0
        UV_names = sort_uv_names(me.uv_layers.keys())
        used_channels = set()
        for layer_name in UV_names:
            match = re.fullmatch(r'UVMap\.(\d+)', layer_name)
            uv_index = int(match.group(1)) if match else (0 if layer_name == 'UVMap' else
                       next((index for index in range(NUMMESHTCH) if index not in used_channels), NUMMESHTCH))
            while uv_index in used_channels:
                uv_index += 1
            if uv_index >= NUMMESHTCH:
                raise ValueError(f'{obj.name}: UV channel exceeds the DAG limit of {NUMMESHTCH}')
            used_channels.add(uv_index)
            layer = me.uv_layers[layer_name]
            if len(layer.data) == 0:
                break#empty layer?
            for tri in triangles:
                meshExp.uv_poly[uv_index].append(meshExp.addUV(layer.data[tri.loop_indices[0]].uv, uv_index))
                meshExp.uv_poly[uv_index].append(meshExp.addUV(layer.data[tri.loop_indices[2]].uv, uv_index))
                meshExp.uv_poly[uv_index].append(meshExp.addUV(layer.data[tri.loop_indices[1]].uv, uv_index))
            uv_index += 1
        for attribute in me.attributes:
            match = re.fullmatch(r'dagor_map_(\d+)', attribute.name)
            if not match:
                continue
            channel = int(match.group(1))
            if not 1 <= channel <= NUMMESHTCH or attribute.data_type != 'FLOAT_VECTOR' or attribute.domain not in {'POINT', 'CORNER'}:
                raise ValueError(f'{obj.name}: invalid mapping attribute {attribute.name}')
            points, indices, lookup = [], [], {}
            for triangle in triangles:
                for corner in (triangle.loop_indices[0], triangle.loop_indices[2], triangle.loop_indices[1]):
                    index = corner if attribute.domain == 'CORNER' else me.loops[corner].vertex_index
                    value = tuple(attribute.data[index].vector)
                    if value not in lookup:
                        lookup[value] = len(points)
                        points.append(value)
                    indices.append(lookup[value])
            meshExp.map_channels[channel] = (points, indices)
#Vertex Colors
        if me.color_attributes.__len__()>0:
            color_attributes_fix_domain(exp_obj)  # making sure that vcol stored in face corners and not somewhere else
            color_attributes = me.color_attributes[0]
            for tri in triangles:
                d = color_attributes.data[tri.loop_indices[0]]
                if d is not None:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor(d.color_srgb))
                else:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor([1.0, 1.0, 1.0]))
                d = color_attributes.data[tri.loop_indices[2]]
                if d is not None:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor(d.color_srgb))
                else:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor([1.0, 1.0, 1.0]))
                d = color_attributes.data[tri.loop_indices[1]]
                if d is not None:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor(d.color_srgb))
                else:
                    meshExp.color_attributes_poly.append(meshExp.addVertexColor([1.0, 1.0, 1.0]))
        node.mesh = meshExp
        if armatures:
            node.skin = collect_skin(exp_obj, armatures[0], self.bone_ids,
                                     getattr(self, 'origin_inverse', None))

    def generateMatScript(self, mat):
        DM = mat.dagormat
        optional = DM.optional
        dagormat_scripts = []
        if DM.sides == 2:
            dagormat_scripts.append("real_two_sided=yes")
        for key in optional.keys():
            prop_string = dagormat_prop_to_string(optional, key, short = True)
            dagormat_scripts.append(prop_string)
        return "\r\n".join(dagormat_scripts)

    def saveMesh(self, node):
        # serialize
        nodeChunkPos = self.writer.beginChunk(DAG_NODE)
        nodeDataChunkPos = self.writer.beginChunk(DAG_NODE_DATA)
        node.objFlg |= DAG_NF_RCVSHADOW
        self.writer.writeDagNodeData(node.id, len(node.children), node.objFlg)
        if node.name.startswith('occluder_box'):
            self.writer.writeStr('occluder_box')
        #removing indecies and types of converted cmp nodes
        elif bpy.data.scenes[0].dag4blend.exporter.cleanup_names:
            name = node.name
            #-index
            if name[-4]=='.' and name[-3:].isnumeric():
                name = name[:-4]
            if name[-6:-2]=='.lod' and name[-2:].isnumeric():
                name = name[:-6]
            #-type
            if name.find(':')>-1:
                name = name[:name.find(':')]
            err = self.writer.writeStr(name)
            if err is not None:
                log(f'{err}\n', type = 'ERROR', show = True)
        else:
            err = self.writer.writeStr(node.name)
            if err is not None:
                log(f'{err}\n', type = 'ERROR', show = True)
        self.writer.endChunk(nodeDataChunkPos)

        if len(node.objProps):
            scriptChunkPos = self.writer.beginChunk(DAG_NODE_SCRIPT)
            self.writer.writeStr(node.objProps)
            self.writer.endChunk(scriptChunkPos)

        materialChunkPos = self.writer.beginChunk(DAG_NODE_MATER)
        for mat_ind in node.materials_indices:
            self.writer.writeUShort(mat_ind)
        self.writer.endChunk(materialChunkPos)

        tmChunkPos = self.writer.beginChunk(DAG_NODE_TM)
        self.writer.writeMatrix4x3(node.tm)
        self.writer.endChunk(tmChunkPos)

        self.writeMesh(node.mesh, node.skin)

        self.saveChildren(node)
        self.writer.endChunk(nodeChunkPos)

    def saveChildren(self, node):
        if len(node.children):
            childNodeChunkPos = self.writer.beginChunk(DAG_NODE_CHILDREN)
            for node in node.children:
                self.saveNode(node)
            self.writer.endChunk(childNodeChunkPos)

    def saveCurve(self, node):
        nodeChunkPos = self.writer.beginChunk(DAG_NODE)
        nodeDataChunkPos = self.writer.beginChunk(DAG_NODE_DATA)
        flg = node.objFlg
        self.writer.writeDagNodeData(node.id, len(node.children), flg)
        self.writer.writeStr(node.name)
        self.writer.endChunk(nodeDataChunkPos)

        if node.objProps:
            script_pos = self.writer.beginChunk(DAG_NODE_SCRIPT)
            self.writer.writeStr(node.objProps)
            self.writer.endChunk(script_pos)

        tmChunkPos = self.writer.beginChunk(DAG_NODE_TM)
        self.writer.writeMatrix4x3(node.tm)
        self.writer.endChunk(tmChunkPos)

        self.writeCurves(node.curves)

        self.saveChildren(node)
        self.writer.endChunk(nodeChunkPos)

    def saveNode(self, node):
        print("Saving object %s" % node.name)
        if node.mesh:
            self.saveMesh(node)
        elif node.curves:
            self.saveCurve(node)
        else:
            self.saveHelper(node)

    def saveHelper(self, node):
        node_pos = self.writer.beginChunk(DAG_NODE)
        data_pos = self.writer.beginChunk(DAG_NODE_DATA)
        flags = node.objFlg if node.light is not None else 0
        self.writer.writeDagNodeData(node.id, len(node.children), flags)
        self.writer.writeStr(node.name)
        self.writer.endChunk(data_pos)
        if node.objProps:
            script_pos = self.writer.beginChunk(DAG_NODE_SCRIPT)
            self.writer.writeStr(node.objProps)
            self.writer.endChunk(script_pos)
        tm_pos = self.writer.beginChunk(DAG_NODE_TM)
        self.writer.writeMatrix4x3(node.tm)
        self.writer.endChunk(tm_pos)
        if node.light is not None:
            obj_pos = self.writer.beginChunk(DAG_NODE_OBJ)
            light_pos = self.writer.beginChunk(DAG_OBJ_LIGHT)
            self.writer.file.write(node.light.to_bytes())
            self.writer.endChunk(light_pos)
            self.writer.endChunk(obj_pos)
        self.saveChildren(node)
        self.writer.endChunk(node_pos)

    def saveNodes(self, parent):
        nodeChunkPos = self.writer.beginChunk(DAG_NODE)
        nodeDataChunkPos = self.writer.beginChunk(DAG_NODE_DATA)
        self.writer.writeDagNodeData(0xFFFF, len(parent.children), 0)
        self.writer.endChunk(nodeDataChunkPos)

        self.saveChildren(parent)
        self.writer.endChunk(nodeChunkPos)

    def saveTextures(self):
        texChunkPos = self.writer.beginChunk(DAG_TEXTURES)
        print(list(self.materials))
        for m in self.materials:
            T = self.materials[m].mat.dagormat.textures
            for i in range(DAGTEXNUM):
                attr_name = "tex" + str(i)
                if hasattr(T, attr_name):
                    texture_path = getattr(T, attr_name)
                    if texture_path and texture_path not in self.textures:
                        self.textures.append(texture_path)
        self.writer.writeUShort(len(self.textures))
        for tex in self.textures:
            if tex.startswith('//'):
                abs_tex = bpy.path.abspath(tex)
                if abs_tex[1]!=':':#still doesn't start with drive letter
                    abs_tex = ensure_no_path(tex)
                self.writer.writeDAGString(abs_tex)
            else:
                self.writer.writeDAGString(tex)
        self.writer.endChunk(texChunkPos)

    def saveMaterials(self):
        for m in self.materials.values():
            mat = m.mat
            DM=mat.dagormat
            matChunkPos = self.writer.beginChunk(DAG_MATER)
            self.writer.writeDAGString(mat.name)
            self.writer.writeColor(DM.ambient)
            self.writer.writeColor(DM.diffuse)
            self.writer.writeColor(DM.specular)
            self.writer.writeColor(DM.emissive)
            self.writer.writeFloat(DM.power)
            # flags
            flags = DAG_MF_16TEX  # should be always used
            if DM.sides == 1:
                flags |= DAG_MF_2SIDED
            self.writer.writeDWord(flags)
            for i in range(DAGTEXNUM):
                if DM.is_proxy:
                        self.writer.writeUShort(DAGBADMATID)  # proxy uses textures from blk, not from dagormat itself
                else:
                    attr_name = "tex" + str(i)
                    if hasattr(mat.dagormat.textures, attr_name):
                        texture_path = getattr(mat.dagormat.textures, attr_name)
                        if not texture_path:
                            self.writer.writeUShort(DAGBADMATID)
                        q = 0
                        for tex in self.textures:
                            if texture_path == tex:
                                self.writer.writeUShort(q)
                                break
                            q += 1
                    else:
                        self.writer.writeUShort(DAGBADMATID)
            # _resv
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            self.writer.writeUShort(0)
            # classname
            if mat.dagormat.is_proxy:
                self.writer.writeDAGString(mat.name+':proxymat')
            else:
                self.writer.writeDAGString(mat.dagormat.shader_class)
                self.writer.writeStr(self.generateMatScript(mat))
            self.writer.endChunk(matChunkPos)

    def enumerate(self, whole_list, objs, parent, scene, origin_inverse=None):
        objects = objs
        for o in objects:
            self.last_index += 1

            node = NodeExp()
            node.name = o.name
            node.id = self.last_index
            if hasattr(self, 'object_ids'):
                node.id = self.object_ids[o]
            node.parent_id = parent.id
            node_parent = parent
            if (o.parent is None) or (o.parent.type not in SUPPORTED_TYPES) or (o.parent not in whole_list):
                node.tm = o.matrix_world.copy()
                if origin_inverse is not None:
                    node.tm = origin_inverse @ node.tm
            else:
                # matrix_local includes matrix_parent_inverse and can differ
                # from the transform relative to the exported parent.
                node.tm = o.parent.matrix_world.inverted_safe() @ o.matrix_world
                if o.parent_type == 'BONE' and o.parent.type == 'ARMATURE':
                    node_parent = self.bone_nodes[o.parent, o.parent_bone]
                    node.parent_id = node_parent.id
                    bone_world = o.parent.matrix_world @ native_pose_matrix(o.parent.pose.bones[o.parent_bone])
                    node.tm = bone_world.inverted_safe() @ o.matrix_world
            ok_matrix = is_matrix_ok(o.matrix_local)
            if ok_matrix is not True:
                msg = f"node {o.name} has incorrect matrix: {ok_matrix}\n"
                log(msg, type = 'ERROR')

            if node_parent.parent_id == -1:
                tmp_r = node.tm[1].copy()
                node.tm[1] = node.tm[2].copy()
                node.tm[2] = tmp_r.copy()
            node.tm.transpose()

            node_parent.children.append(node)
            self.nodes.append(node)
            if o.type == 'MESH':
                self.dumpMesh(o, node, scene)
            elif o.type == 'CURVE':
                self.dumpCurve(o, node, scene)
                node.objProps = self.gatherObjPropScript(o, node)
            if o.type in {'EMPTY', 'LIGHT', 'ARMATURE', 'CAMERA'}:
                node.objProps = self.gatherObjPropScript(o, node)
                if o.type == 'ARMATURE':
                    self.enumerate_bones(o, node)
                if o.type == 'LIGHT':
                    try:
                        node.light = DagLight.from_blender(o.data)
                    except ValueError as error:
                        log(f'{error}\n', type='ERROR', show=True)
                        return -1
                    node.objFlg &= ~DAG_NF_RENDERABLE
            elif node.mesh is None and node.curves is None:
                return -1
            child_list=list(ob for ob in o.children if ob in whole_list)
            if self.enumerate(whole_list, child_list, node, scene, origin_inverse) == -1:
                return -1
        return 0

    def enumerate_bones(self, armature, parent_node):
        nodes = {}
        for bone in armature.data.bones:
            node = NodeExp()
            node.id = self.bone_ids[armature, bone.name]
            node.name = bone.name
            properties = parse_properties(bone.get('dagor_script', ''))
            properties['dagor_bone:b'] = True
            node.objProps = serialize_properties(properties)
            node.tm = effective_bind(bone)
            if bone.parent is not None:
                node.tm = effective_bind(bone.parent).inverted() @ node.tm
            node.tm.transpose()
            nodes[bone.name] = node
            self.bone_nodes[armature, bone.name] = node
            self.nodes.append(node)
        for bone in armature.data.bones:
            parent = nodes[bone.parent.name] if bone.parent else parent_node
            node = nodes[bone.name]
            node.parent_id = parent.id
            parent.children.append(node)

    def export_dag(self,whole_list,filepath, origin_inverse=None):
        objects_before = set(bpy.data.objects)
        meshes_before = set(bpy.data.meshes)
        materials_before = set(bpy.data.materials)
        selected_before = list(bpy.context.selected_objects)
        active_before = bpy.context.view_layer.objects.active
        self.temp_export_path = None
        try:
            if origin_inverse is None and self.origin_name:
                origin = bpy.data.objects.get(self.origin_name)
                if origin is None or origin.name not in bpy.context.scene.objects:
                    raise ValueError('Export origin must be an object in the current scene')
                origin_inverse = origin.matrix_world.inverted()
            # A selected skinned mesh must carry its skeleton even when the
            # armature itself was not explicitly selected.
            whole_list = list(dict.fromkeys(whole_list))
            for obj in list(whole_list):
                if obj.parent_type == 'BONE' and obj.parent is not None and obj.parent.type == 'ARMATURE':
                    if obj.parent not in whole_list:
                        whole_list.append(obj.parent)
                if obj.type != 'MESH':
                    continue
                for modifier in obj.modifiers:
                    if modifier.type == 'ARMATURE' and modifier.show_viewport and modifier.object is not None:
                        if modifier.object not in whole_list:
                            whole_list.append(modifier.object)
            return self._export_dag(whole_list, filepath, origin_inverse)
        except Exception as error:
            log(f'DAG export failed: {error}\n', type='ERROR', show=True)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}
        finally:
            if self.writer.file is not None and not self.writer.file.closed:
                self.writer.close()
            if self.temp_export_path is not None and exists(self.temp_export_path):
                unlink(self.temp_export_path)
            for obj in set(bpy.data.objects) - objects_before:
                bpy.data.objects.remove(obj, do_unlink=True)
            for mesh in set(bpy.data.meshes) - meshes_before:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            for material in set(bpy.data.materials) - materials_before:
                if material.users == 0:
                    bpy.data.materials.remove(material)
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_before:
                if obj.name in bpy.context.view_layer.objects:
                    obj.select_set(True)
            if active_before is not None and active_before.name in bpy.context.view_layer.objects:
                bpy.context.view_layer.objects.active = active_before

    def _export_dag(self,whole_list,filepath, origin_inverse=None):
        # Every file has its own node ID space and material/texture tables.
        self.last_index = 0
        self.nodes = []
        self.materials = {}
        self.textures = []
        self.origin_inverse = origin_inverse
        self.object_ids = {obj: index for index, obj in enumerate(whole_list)}
        self.bone_ids = {}
        self.bone_nodes = {}
        next_id = len(self.object_ids)
        for obj in whole_list:
            if obj.type == 'ARMATURE':
                for bone in obj.data.bones:
                    self.bone_ids[obj, bone.name] = next_id
                    next_id += 1
        if next_id > 65535:
            log('DAG has too many object and bone nodes (maximum 65535)\n', type='ERROR', show=True)
            return {'CANCELLED'}
        existing_objects = list(ob  for ob  in bpy.data.objects)
        existing_mats = list(mat for mat in bpy.data.materials)
        filepath = abspath(ensure_ext(filepath, self.filename_ext))
        filename = ensure_no_path(filepath)
        makedirs(dirname(filepath), exist_ok=True)
        with NamedTemporaryFile(dir=dirname(filepath), prefix='.dag4blend-', suffix='.dag', delete=False) as temporary:
            filepath_temp = self.temp_export_path = temporary.name
        log(f'EXPORTING {filepath}\n')
        objs=list(ob for ob in whole_list if ob.parent is None or ob.parent not in whole_list)
        if objs.__len__() == 0:
            err = 'No objects to export in ' + ensure_no_path(filepath)
            show_popup(message=err,icon='ERROR',title='Error!')
            log(f'{err}\n', type = 'ERROR', show = True)
            return{'CANCELLED'}
        S = bpy.context.scene
        print("Blender Version {}.{}.{}".format(bpy.app.version[0], bpy.app.version[1], bpy.app.version[2]))
        print("Filepath: {}".format(filepath))
        print("Writing DAG file...")
        self.writer.open(filepath_temp)
        self.writer.writeHeader(DAG_ID)
        node = self.createRootNode()
        dagChunkPos = self.writer.beginChunk(DAG_ID)

        if self.enumerate(whole_list,objs, node, S, origin_inverse) == -1:
            log("Failed to enumerate objects\n", type = 'ERROR', show = True)
            self.writer.close()
            return {'CANCELLED'}

        self.saveTextures()
        self.saveMaterials()
        self.saveNodes(node)
        self.writer.endChunk(dagChunkPos)
        dagEndChunkPos = self.writer.beginChunk(DAG_END)
        self.writer.endChunk(dagEndChunkPos)
        self.writer.close()
        dirpath = dirname(filepath)
        if not exists(dirpath):
            makedirs(dirpath)
        replace(filepath_temp, filepath)
        #no need to delete temporary dag, it will be auto-removed with bpy.app.tempdir on blender being closed/crushed
        #cleanup part. Let's remove temporary stuff
        filename = ensure_no_path(filepath)
        occluders = 0
        for obj in bpy.data.objects:
            if obj not in existing_objects:
                if obj.name.startswith('occluder_box'):
                    occluders+=1
                bpy.data.meshes.remove(obj.data)
        if occluders>2:# one copy for export preparation, one for triangulation data
            log(f'{filename}: {occluders/2} occluders in one dag\n', type = 'WARNING', show = True)
        for mat in bpy.data.materials:
            if mat not in existing_mats:
                bpy.data.materials.remove(mat)
        print(filename+' exported')
        self.materials = {}#we don't need this for next dag.
        self.textures = []
        log(f'{filename}: export FINISHED\n')
        return {'FINISHED'}

    def export_collection(self,col,dirpath):
        if not self.collection_visible(col):
            return {'FINISHED'}
        #object outside of collections without subcollections
        orphans=self.orphans
        if col.children.__len__()>0:
            if orphans:
                for obj in col.objects:
                    if self.is_exportable(obj):
                        filepath=join(dirpath,obj.name+'.dag')
                        if self.export_dag([obj],filepath) == {'CANCELLED'}:
                            return {'CANCELLED'}
            for child in col.children:
                if self.export_collection(child,dirpath) == {'CANCELLED'}:
                    return {'CANCELLED'}
        #collection(s) without children, but with objects
        elif col.objects.__len__()>0:
            if "name" in col.keys():
                stored_name = col["name"].replace('\\','/')
                #separator in the beginning makes blender save file one directory above export path, we don't need that
                stored_name = stored_name.lstrip('/')
                subpath = stored_name.replace('*',col.name)
                if len(subpath) > 1 and subpath[1]==':':#drive
                    filepath = subpath
                else:
                    filepath = join(dirpath,subpath)
            else:
                filepath=join(dirpath,col.name)
            whole_list=list(ob for ob in col.objects if self.is_exportable(ob))
            filepath = bpy.path.ensure_ext(filepath,'.dag')
            if whole_list:
                return self.export_dag(whole_list,filepath)
        return {'FINISHED'}

    def collection_visible(self, collection):
        if self.include_hidden:
            return True
        if collection.hide_viewport:
            return False
        visibility = []
        def visit(layer, parent_visible):
            visible = parent_visible and not layer.hide_viewport and not layer.exclude
            if layer.collection == collection:
                visibility.append(visible)
            for child in layer.children:
                visit(child, visible)
        visit(bpy.context.view_layer.layer_collection, True)
        return any(visibility)

    def collection_objects(self, collection):
        if not self.collection_visible(collection):
            return []
        objects = [obj for obj in collection.objects if self.is_exportable(obj)]
        for child in collection.children:
            objects.extend(self.collection_objects(child))
        return list(dict.fromkeys(objects))

    def export_legacy(self, context, filepath):
        base = re.sub(r'(?:\.lod00)?\.dag$', '', filepath, flags=re.IGNORECASE)
        outputs = set()
        plans = []
        for collection in context.scene.collection.children_recursive:
            suffix = legacy_variation_suffix(collection.name)
            if suffix is None or not self.collection_visible(collection):
                continue
            objects = [obj for obj in collection.objects if self.is_exportable(obj)
                       and (not self.legacy_selected_only or obj.select_get())]
            if not objects:
                continue
            destination = base + suffix
            if destination.casefold() in outputs:
                self.report({'ERROR'}, f'Legacy collections resolve to the same output: {destination}')
                return {'CANCELLED'}
            outputs.add(destination.casefold())
            plans.append((objects, destination))
        if not plans:
            self.report({'ERROR'}, 'No legacy LOD or variation collections contain exportable objects')
            return {'CANCELLED'}
        for objects, destination in plans:
            if self.export_dag(objects, destination) == {'CANCELLED'}:
                return {'CANCELLED'}
        return {'FINISHED'}

    def is_exportable(self, obj):
        enabled = {'MESH': self.meshes, 'EMPTY': self.helpers, 'ARMATURE': self.helpers,
                   'LIGHT': self.lights, 'CURVE': self.curves, 'CAMERA': self.cameras}
        return enabled.get(obj.type, False) and (self.include_hidden or obj.visible_get())

    def execute(self, context):
        mode = self.limits
        filepath = self.filepath
        dirpath=dirname(filepath)
        P = bpy.data.scenes[0].dag4blend.exporter
        try:
            bpy.ops.object.mode_set(mode='OBJECT')
        except Exception:
            pass
        VL=context.view_layer
        if mode == 'Legacy':
            return self.export_legacy(context, filepath)
        if   mode=='Visible':
            whole_list = list(ob for ob in VL.objects if self.is_exportable(ob))
            return self.export_dag(whole_list,filepath)
        elif mode=='Sel.Joined':
            whole_list = list(ob for ob in VL.objects if ob.select_get() and self.is_exportable(ob))
            return self.export_dag(whole_list,filepath)
        elif mode=='Sel.Separated':
            selected = [ob for ob in VL.objects if ob.select_get() and self.is_exportable(ob)]
            # Selected helpers act as Max groups: export their descendants
            # together, relative to the helper pivot, once per selected root.
            grouped = {child for ob in selected if ob.type == 'EMPTY'
                       for child in ob.children_recursive}
            for obj in selected:
                if obj in grouped:
                    continue
                whole_list = [obj]
                if obj.type == 'EMPTY':
                    whole_list.extend(child for child in obj.children_recursive
                                      if self.is_exportable(child))
                if self.include_collisions:
                    collision_name = (self.collision_prefix + obj.name).casefold()
                    for candidate in context.scene.objects:
                        name = candidate.name.casefold()
                        if self.is_exportable(candidate) and (name == collision_name or name.startswith(collision_name + '_')):
                            whole_list.append(candidate)
                            if candidate.type == 'EMPTY':
                                whole_list.extend(child for child in candidate.children_recursive if self.is_exportable(child))
                filename = self.filename_prefix + obj.name + self.filename_suffix
                if any(character in filename for character in '<>:"/\\|?*'):
                    self.report({'ERROR'}, f'Invalid output filename: {filename}')
                    return {'CANCELLED'}
                filepath = join(dirpath, filename)
                if self.export_dag(whole_list, filepath, obj.matrix_world.inverted_safe()) == {'CANCELLED'}:
                    return {'CANCELLED'}
        elif mode=='Col.Separated':
            dag_col=P.collection
            if dag_col==None:
                if context.scene.collection.children.__len__()==0:
                    show_popup(message="No sub-collections found. 'Scene Collection.dag' not exported")
                    return {'CANCELLED'}
                else:
                    for child in context.scene.collection.children:
                        if self.export_collection(child,dirpath) == {'CANCELLED'}:
                            return {'CANCELLED'}
            else:
                return self.export_collection(dag_col,dirpath)
        elif mode =='Col.Joined':
            dag_col=P.collection
            if dag_col==None:
                show_popup(message="Doesn't work for Scenre Collection",icon='ERROR')
                return{'CANCELLED'}
            filepath=join(dirpath,dag_col.name)
            whole_list=self.collection_objects(dag_col)
            return self.export_dag(whole_list,filepath)
        return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(DagExporter.bl_idname, text='Dagor Engine (.dag)')

def register():
    bpy.utils.register_class(DagExporter)
    bpy.utils.register_class(DAG_PT_export)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_import)
    bpy.utils.unregister_class(DAG_PT_export)
    bpy.utils.unregister_class(DagExporter)
