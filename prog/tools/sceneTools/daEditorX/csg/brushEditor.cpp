// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "brushEditor.h"
#include "objEd_csg.h"
#include "plugin.h"
#include <EditorCore/ec_IEditorCore.h>
#include <EditorCore/ec_cm.h>
#include <libTools/staticGeom/geomObject.h>
#include <libTools/staticGeom/staticGeometryContainer.h>
#include <libTools/ObjCreator3d/objCreator3d.h>
#include <libTools/util/undo.h>
#include <unwrapMapping/autoUnwrap.h>
#include <de3_assetService.h>
#include <de3_interface.h>
#include <de3_csgCollision.h>
#include <de3_primitiveGeometry.h>
#include <ioSys/dag_dataBlock.h>
#include <oldEditor/de_workspace.h>
#include <startup/dag_globalSettings.h>
#include <imgui/imgui.h>
#include <propPanel/propPanel.h>
#include <propPanel/propPanelService.h>
#include <winGuiWrapper/wgw_dialogs.h>
#include <algorithm>
#include <chrono>
#include <charconv>
#include <cmath>
#include <cstdio>
#include <functional>
#include <locale>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>

using editorcore_extapi::dagGeom;
using editorcore_extapi::dagRender;
void runLegacyCSGAcceptance();
namespace
{
struct UiEditFinished {};
std::string doubleSetting(double value)
{
  char buffer[64]; auto result=std::to_chars(buffer,buffer+sizeof(buffer),value);
  return std::string(buffer,result.ptr);
}
bool readDoubleSetting(const DataBlock &settings,const char *key,double fallback,double &value)
{
  std::string exactKey=std::string(key)+"Exact";
  const char *exact=settings.getStr(exactKey.c_str(),nullptr);
  char legacy[64];
  if(!exact)
  {
    // BLK reals are floats. Decode their shortest decimal value rather than
    // promoting the binary rounding error into the double precision grid.
    auto result=std::to_chars(legacy,legacy+sizeof(legacy),settings.getReal(key,float(fallback)));
    if(result.ec!=std::errc{}) return false;
    std::string text(legacy,result.ptr); auto parsed=std::from_chars(text.data(),text.data()+text.size(),value);
    return parsed.ec==std::errc{} && parsed.ptr==text.data()+text.size() && std::isfinite(value);
  }
  auto end=exact+strlen(exact); auto parsed=std::from_chars(exact,end,value);
  return parsed.ec==std::errc{} && parsed.ptr==end && std::isfinite(value);
}
struct OnExit { std::function<void()> callback; ~OnExit() { callback(); } };
struct TreeScope {
  bool open;
  explicit TreeScope(const char *label):open(ImGui::TreeNode(label)) {}
  ~TreeScope() { if(open) ImGui::TreePop(); }
  explicit operator bool() const { return open; }
};
Point3 point(csg::Vec p) { return Point3(float(p.x),float(p.y),float(p.z)); }
csg::Vec vec(Point3 p) { return {p.x,p.y,p.z}; }
csg::Transform compose(const csg::Transform &a,const csg::Transform &b)
{
  csg::Transform r; for (unsigned i=0;i<3;++i) r.column[i]=a.vector(b.column[i]); r.column[3]=a.point(b.column[3]); return r;
}
csg::Node *parentOf(csg::Node &root,csg::Id id)
{
  for (auto &n:root.children) { if (n.id==id) return &root; if (auto *p=parentOf(n,id)) return p; } return nullptr;
}
class BrushUndo final : public UndoRedoObject
{
  BrushEditor &editor;
  csg::Document before,after;
  std::pair<int,float> beforeMapping,afterMapping;
public:
  BrushUndo(BrushEditor &e,csg::Document b,csg::Document a):BrushUndo(e,std::move(b),std::move(a),e.mappingSettings()) {}
  BrushUndo(BrushEditor &e,csg::Document b,csg::Document a,std::pair<int,float> mapping):
    editor(e),before(std::move(b)),after(std::move(a)),beforeMapping(mapping),afterMapping(e.mappingSettings()) {}
  void restore(bool saveRedo) override {
    if (saveRedo) { after=editor.document; afterMapping=editor.mappingSettings(); }
    editor.restore(before); editor.restoreMappingSettings(beforeMapping);
  }
  void redo() override { editor.restore(after); editor.restoreMappingSettings(afterMapping); }
  size_t size() override
  {
    std::function<size_t(const csg::Node &)> storage=[&](const csg::Node &node) {
      size_t bytes=node.name.capacity()+1+node.meshSource.capacity()+1+node.cutSurface.material.capacity()+1;
      bytes+=node.children.capacity()*sizeof(csg::Node)+node.brush.vertices.capacity()*sizeof(csg::Vec)+
        node.brush.faces.capacity()*sizeof(csg::Face);
      bytes+=node.extrusion.polygon.capacity()*sizeof(csg::Vec)+node.extrusion.path.capacity()*sizeof(csg::CurvePoint)+
        node.extrusionSurfaces.capacity()*sizeof(csg::Id)+node.extrusion.surface.material.capacity()+1;
      bytes+=node.extrusion.surfaces.capacity()*sizeof(csg::Extrusion::FaceSettings);
      for(const auto &face:node.extrusion.surfaces) bytes+=face.surface.material.capacity()+1;
      for(const auto &face:node.brush.faces)
        bytes+=face.vertices.capacity()*sizeof(uint32_t)+face.surface.material.capacity()+1;
      for(const auto &child:node.children) bytes+=storage(child);
      return bytes;
    };
    return sizeof(*this)+storage(before.root)+storage(after.root);
  }
  void accepted() override {}
  void get_description(String &s) override { s="CSG brush document"; }
};
class BrushGizmo final : public RenderableEditableObject
{
  BrushEditor &editor;
public:
  explicit BrushGizmo(BrushEditor &e):editor(e) { setName("CSG brush selection"); }
  void update(float) override {}
  void beforeRender() override {}
  void render() override {}
  void renderTrans() override {}
  bool isSelectedByRectangle(IGenViewportWnd *,const EcRect &) const override { return false; }
  bool isSelectedByPointClick(IGenViewportWnd *,int,int) const override { return false; }
  bool getWorldBox(BBox3 &box) const override { return editor.selectionBounds(box); }
  bool mayDelete() override { return false; }
  bool mayRename() override { return false; }
  void onPPChange(int,bool,PropPanel::ContainerPropertyControl &,dag::ConstSpan<RenderableEditableObject *>) override {}
  void moveObject(const Point3 &d,IEditorCoreEngine::BasisType b) override
  { TMatrix before=getWtm(); RenderableEditableObject::moveObject(d,b); editor.transformSelection(before,getWtm()); }
  void rotateObject(const Point3 &d,const Point3 &o,IEditorCoreEngine::BasisType b) override
  { TMatrix before=getWtm(); RenderableEditableObject::rotateObject(d,o,b); editor.transformSelection(before,getWtm()); }
  void scaleObject(const Point3 &d,const Point3 &o,IEditorCoreEngine::BasisType b) override
  { TMatrix before=getWtm(); RenderableEditableObject::scaleObject(d,o,b); editor.transformSelection(before,getWtm()); }
  void putMoveUndo() override { editor.putTransformUndo(); }
  void putRotateUndo() override { editor.putTransformUndo(); }
  void putScaleUndo() override { editor.putTransformUndo(); }
};
bool inputDouble(const char *label,double &v,double step=0)
{ return ImGui::InputDouble(label,&v,step,0,"%.9g"); }
bool shapeButton(const char *label,const char *iconName,const char *hint)
{
  float iconSize=ImGui::GetTextLineHeight(); auto pos=ImGui::GetCursorScreenPos(); auto pad=ImGui::GetStyle().FramePadding;
  auto *service=DAEDITOR3.getPropPanelService(); auto texture=service ? service->getIconTextureId(iconName,int(iconSize)):nullptr;
  ImGui::PushStyleVar(ImGuiStyleVar_ButtonTextAlign,ImVec2(1,0.5f));
  bool clicked=ImGui::Button(label,ImVec2(ImGui::CalcTextSize(label).x+iconSize+ImGui::GetStyle().ItemInnerSpacing.x+pad.x*2,iconSize+pad.y*2));
  ImGui::PopStyleVar();
  if(texture) ImGui::GetWindowDrawList()->AddImage(texture,
    ImVec2(pos.x+pad.x,pos.y+pad.y),ImVec2(pos.x+pad.x+iconSize,pos.y+pad.y+iconSize));
  if(ImGui::IsItemHovered()) ImGui::SetTooltip("%s",hint);
  return clicked;
}
bool inputVec(const char *label,csg::Vec &v)
{
  double a[]={v.x,v.y,v.z}; bool changed=ImGui::InputScalarN(label,ImGuiDataType_Double,a,3,nullptr,nullptr,"%.9g");
  if (changed) v={a[0],a[1],a[2]}; return changed;
}
bool rayTriangle(csg::Vec o,csg::Vec d,csg::Vec a,csg::Vec b,csg::Vec c,double &distance)
{
  auto e=b-a,f=c-a,p=csg::cross(d,f); double det=csg::dot(e,p);
  if (std::abs(det)<1e-12) return false;
  double u=csg::dot(o-a,p)/det; if (u<0 || u>1) return false;
  auto q=csg::cross(o-a,e); double v=csg::dot(d,q)/det; if (v<0 || u+v>1) return false;
  double t=csg::dot(f,q)/det; if (t<0 || t>=distance) return false; distance=t; return true;
}
struct MappingSnapshot
{
  std::vector<unsigned short> pages;
  std::vector<TFace> faces;
  std::vector<Point2> vertices;
};
MappingSnapshot mappingSnapshot(Mesh input,int size,float sample,bool memory,float scale)
{
  if(memory) AutoUnwrapMapping::start_mapping_in_memory(size); else AutoUnwrapMapping::start_mapping(size);
  OnExit finish{[] { AutoUnwrapMapping::finish_mapping(); }};
  QuietProgressIndicator progress; SimpleProgressCB cancel;
  int handle=AutoUnwrapMapping::request_mapping(input.face.data(),input.face.size(),input.vert.data(),input.vert.size(),sample,false,0);
  AutoUnwrapMapping::prepare_facegroups(progress,cancel);
  // Repack twice to check restoration of originals after UV normalization.
  AutoUnwrapMapping::repack_facegroups(1,nullptr,0,progress,cancel);
  if(AutoUnwrapMapping::repack_facegroups(scale,nullptr,0,progress,cancel)<=0) throw std::runtime_error("Mapping parity packing failed");
  MappingSnapshot r; r.pages.resize(input.face.size()); r.faces.resize(input.face.size());
  Point2 *uv=nullptr; int count=0;
  AutoUnwrapMapping::get_final_mapping(handle,r.pages.data(),sizeof(unsigned short),r.faces.data(),uv,count);
  if(!uv || count<=0) throw std::runtime_error("Mapping parity produced no UVs");
  r.vertices.assign(uv,uv+count); return r;
}
bool mappingEqual(const MappingSnapshot &a,const MappingSnapshot &b)
{
  if(a.pages!=b.pages || a.faces.size()!=b.faces.size() || a.vertices.size()!=b.vertices.size()) return false;
  for(size_t i=0;i<a.faces.size();++i) for(unsigned j=0;j<3;++j) if(a.faces[i].t[j]!=b.faces[i].t[j]) return false;
  for(size_t i=0;i<a.vertices.size();++i) if(a.vertices[i].x!=b.vertices[i].x || a.vertices[i].y!=b.vertices[i].y) return false;
  return true;
}
}
BrushEditor::BrushEditor(ObjEd &e):owner(e)
{
  reset();
}
BrushEditor::~BrushEditor()
{
  for (auto &part:parts) if (part.second.geometry) dagGeom->deleteGeomObject(part.second.geometry);
  if (gizmo && gizmo->getObjEditor()==&owner) owner.removeObject(gizmo,false);
  if (preview) dagGeom->deleteGeomObject(preview);
  delete published; delete unreadDocument;
}
void BrushEditor::reset()
{
  for (auto &part:parts) if (part.second.geometry) dagGeom->deleteGeomObject(part.second.geometry);
  parts.clear();
  document={}; document.root.name="CSG Model"; document.assignIds(document.root); selected=document.root.id;
  evaluator.clear(); current={}; components.clear(); editErrors.clear(); dirty=true; loadFailed=false;
  delete unreadDocument; unreadDocument=nullptr;
  if (preview) dagGeom->deleteGeomObject(preview);
  delete published; published=nullptr;
  if (!gizmo) gizmo=new BrushGizmo(*this);
  if (gizmo->getObjEditor()!=&owner) owner.addObject(gizmo,false);
  gizmo->setFlags(0,RenderableEditableObject::FLG_SELECTED,false);
}
void BrushEditor::save(DataBlock &b)
{
  auto &out=*b.addNewBlock("brushDocument");
  if (unreadDocument) out.setFrom(unreadDocument); else csg::saveDocument(benchmarkSource ? *benchmarkSource:document,out);
  auto &settings=*b.addNewBlock("brushEditorSettings"); settings.setInt("lightmapSize",lightmapSize);
  settings.setReal("lightmapSampleSize",lightmapSampleSize); settings.setReal("grid",grid); settings.setReal("angleSnap",angleSnap);
  settings.setStr("gridExact",doubleSetting(grid).c_str()); settings.setStr("angleSnapExact",doubleSetting(angleSnap).c_str());
  settings.setStr("defaultTexture",defaultTexture.c_str());
  settings.setStr("defaultNormalTexture",defaultNormalTexture.c_str());
}
void BrushEditor::load(const DataBlock &b)
{
  reset();
  if (const auto *source=b.getBlockByName("brushDocument"))
    if (!csg::loadDocument(*source,document,editErrors))
    {
      unreadDocument=new DataBlock(*source); loadFailed=true;
      for (const auto &error:editErrors)
        DAEDITOR3.conError("CSG document load: node %llu, face %llu: %s",error.node,error.face,error.message.c_str());
    }
  const auto &settings=*b.getBlockByNameEx("brushEditorSettings");
  lightmapSize=settings.getInt("lightmapSize",1024); lightmapSampleSize=settings.getReal("lightmapSampleSize",0.1f);
  if(!readDoubleSetting(settings,"grid",0.01,grid) || !readDoubleSetting(settings,"angleSnap",15,angleSnap))
  {
    loadFailed=true; editErrors.push_back({csg::Code::InvalidDocument,0,0,"Invalid grid or angle snapping setting"});
  }
  defaultTexture=settings.getStr("defaultTexture","");
  defaultNormalTexture=settings.getStr("defaultNormalTexture","");
  selected=document.root.id; dirty=true;
  acceptanceQueued=!loadFailed && dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgAcceptance",false);
  benchmarkQueued=!loadFailed && dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgBenchmark",false);
  if(benchmarkQueued && !acceptanceQueued) { benchmarkQueued=false; startBenchmark(); }
}
void BrushEditor::restore(csg::Document value)
{
  document=std::move(value); dirty=true; components.clear();
  if(!document.find(selected)) selected=document.root.id;
  syncGizmo(); owner.updateSelection(); owner.updateGizmo();
}
void BrushEditor::edit(const char *label,const std::function<bool()> &action)
{
  if (loadFailed) throw UiEditFinished{};
  auto before=document; auto beforeMapping=mappingSettings(); editErrors.clear();
  if (!action()) { document=std::move(before); restoreMappingSettings(beforeMapping); throw UiEditFinished{}; }
  owner.getUndoSystem()->begin(); owner.getUndoSystem()->put(new BrushUndo(*this,std::move(before),document,beforeMapping));
  owner.getUndoSystem()->accept(label); dirty=true; activateSelection();
  DAGORED2->invalidateViewportCache();
  throw UiEditFinished{}; // Unwind references into vectors changed by this edit.
}
void BrushEditor::add(csg::Mesh mesh,const char *name)
{
  if (!csg::validate(mesh,editErrors,0,true)) return;
  edit("Create CSG brush",[&] {
    auto *parent=document.find(selected); if (!parent || parent->parametric || !parent->brush.faces.empty()) parent=&document.root;
    csg::Node n; n.name=name; n.brush=std::move(mesh); document.assignIds(n); selected=n.id;
    parent->children.push_back(std::move(n)); components.clear(); return true;
  });
}
void BrushEditor::addExtrusion(csg::Extrusion source,const char *name)
{
  editErrors.clear(); csg::Mesh generated;
  if(!csg::generateExtrusion(source,generated,editErrors)) return;
  edit("Create parametric CSG source",[&] {
    auto *parent=document.find(selected); if(!parent || parent->parametric || !parent->brush.faces.empty()) parent=&document.root;
    csg::Node shape; shape.name=name; shape.parametric=true; shape.extrusion=std::move(source);
    document.assignIds(shape); selected=shape.id; parent->children.push_back(std::move(shape)); components.clear(); mode=0; return true;
  });
}
void BrushEditor::addNativeGeometry(const StaticGeometryContainer &source,const char *name,bool preserveSmoothing)
{
  csg::Node group; group.name=name; editErrors.clear();
  for(const auto *node:source.nodes) {
    if(!node->mesh || node->mesh->mesh.face.empty()) continue;
    const auto &mesh=node->mesh->mesh;
    csg::Node brush; brush.name=node->name.str(); brush.closedMesh=true; brush.meshSource=name;
    for(int i=0;i<4;++i) brush.transform.column[i]=vec(node->wtm.getcol(i));
    for(auto p:mesh.vert) brush.brush.vertices.push_back(vec(p));
    for(int i=0;i<mesh.face.size();++i) {
      const auto &triangle=mesh.face[i]; csg::Face face;
        for(auto index:triangle.v) {
          if(index>=brush.brush.vertices.size()) {
            editErrors.push_back({csg::Code::InvalidMesh,0,0,"Imported mesh contains an invalid vertex index"}); return;
          }
          face.vertices.push_back(index);
        }
      if(preserveSmoothing) face.surface.smoothing=triangle.smgr;
      if(mesh.tface[0].size()==mesh.face.size()) {
        csg::Vec uv[3]; bool valid=true;
        for(int j=0;j<3;++j) {
          auto index=mesh.tface[0][i].t[j]; if(index>=mesh.tvert[0].size()) { valid=false; break; }
          auto p=mesh.tvert[0][index]; uv[j]={p.x,p.y,0};
        }
        if(!valid || !csg::mapSurfaceTriangle(face.surface,brush.brush.vertices[triangle.v[0]],brush.brush.vertices[triangle.v[1]],
          brush.brush.vertices[triangle.v[2]],uv[0],uv[1],uv[2])) {
          editErrors.push_back({csg::Code::InvalidMesh,0,0,"Imported mesh contains invalid UV indices or degenerate triangles"}); return;
        }
      }
      brush.brush.faces.push_back(std::move(face));
    }
    if(csg::volume(brush.brush)<0) for(auto &face:brush.brush.faces) std::reverse(face.vertices.begin(),face.vertices.end());
    if(!csg::validateClosedMesh(brush.brush,editErrors)) return;
    group.children.push_back(std::move(brush));
  }
  if(group.children.empty()) { editErrors.push_back({csg::Code::InvalidMesh,0,0,"No closed mesh geometry was found"}); return; }
  edit("Import closed CSG geometry",[&] {
    auto *parent=document.find(selected); if(!parent || parent->parametric || !parent->brush.faces.empty()) parent=&document.root;
    csg::Node added=group.children.size()==1 ? std::move(group.children[0]):std::move(group);
    added.name=name; document.assignIds(added); selected=added.id; parent->children.push_back(std::move(added)); components.clear(); mode=0; return true;
  });
}
void BrushEditor::importClosedMesh()
{
  String filename=wingw::file_open_dlg(nullptr,"Import a closed mesh for CSG","DAG files|*.dag|All files|*.*","dag");
  if(filename.empty()) return;
  StaticGeometryContainer source;
  if(!dagGeom->staticGeometryContainerLoadFromDag(source,filename.str(),nullptr)) {
    editErrors={{csg::Code::InvalidMesh,0,0,"Dagor could not load the selected mesh"}}; return;
  }
  addNativeGeometry(source,filename.str(),true);
}
void BrushEditor::hierarchy(csg::Node &n)
{
  ImGui::PushID(reinterpret_cast<void *>(uintptr_t(n.id)));
  ImGuiTreeNodeFlags flags=ImGuiTreeNodeFlags_OpenOnArrow|ImGuiTreeNodeFlags_DefaultOpen;
  if (n.id==selected) flags|=ImGuiTreeNodeFlags_Selected;
  if (n.children.empty()) flags|=ImGuiTreeNodeFlags_Leaf;
  const char *op=n.operation==csg::Operation::Union ? "+":n.operation==csg::Operation::Subtract ? "-":"&";
  bool open=ImGui::TreeNodeEx("node",flags,"%s %s%s",op,n.name.c_str(),n.visible ? "":" (disabled)");
  if (ImGui::IsItemClicked()) { selected=n.id; components.clear(); faceIndex=0; activateSelection(); }
  if (n.id!=document.root.id && ImGui::BeginDragDropSource())
  { ImGui::SetDragDropPayload("CSG_NODE",&n.id,sizeof(n.id)); ImGui::TextUnformatted(n.name.c_str()); ImGui::EndDragDropSource(); }
  if (!n.parametric && n.brush.faces.empty() && ImGui::BeginDragDropTarget())
  {
    if (auto *payload=ImGui::AcceptDragDropPayload("CSG_NODE"))
    {
      csg::Id moved=*static_cast<const csg::Id *>(payload->Data),target=n.id;
      // Defer hierarchy mutation until recursion unwinds.
      pendingMove=moved; pendingParent=target;
    }
    ImGui::EndDragDropTarget();
  }
  if (open) { for (auto &c:n.children) hierarchy(c); ImGui::TreePop(); }
  ImGui::PopID();
}
void BrushEditor::modelling(csg::Node &n)
{
  if(n.parametric) { extrusionProperties(n); return; }
  if(n.closedMesh) { ImGui::TextWrapped("Closed mesh source. Use the object gizmo, booleans and per-face surfaces. Component modelling is reserved for convex brushes."); return; }
  if (n.brush.faces.empty()) return;
  ImGui::Combo("Selection mode",&mode,"Brush\0Face\0Edge\0Vertex\0");
  ImGui::TextWrapped("Click a brush in the viewport to select a component. Ctrl-click toggles vertices. Component indices refer to source brushes.");
  ImGui::InputInt("Face index",&faceIndex); faceIndex=std::clamp(faceIndex,0,int(n.brush.faces.size())-1);
  std::ostringstream selectedText; for (auto i:components) selectedText<<i<<' ';
  ImGui::Text("Selected vertices: %s",selectedText.str().c_str());
  static int vertexIndex=0;
  ImGui::InputInt("Vertex index",&vertexIndex);
  if (ImGui::Button("Toggle vertex") && vertexIndex>=0 && size_t(vertexIndex)<n.brush.vertices.size())
  {
    auto it=std::find(components.begin(),components.end(),uint32_t(vertexIndex));
    if (it==components.end()) components.push_back(vertexIndex); else components.erase(it);
  }
  static float delta[3]={}; ImGui::InputFloat3("Component offset",delta);
  if (ImGui::Button("Move components")) edit("Move CSG components",[&] {
    auto indices=mode==1 ? n.brush.faces[faceIndex].vertices:components;
    csg::Vec d={delta[0],delta[1],delta[2]};
    if (grid>0) { d.x=std::round(d.x/grid)*grid; d.y=std::round(d.y/grid)*grid; d.z=std::round(d.z/grid)*grid; }
    return !indices.empty() && csg::moveVertices(n.brush,indices,d,editErrors);
  });
  inputDouble("Distance",distance,grid);
  if (ImGui::Button("Push / pull face")) edit("Push/pull CSG face",[&] {
    const auto &f=n.brush.faces[faceIndex];
    auto a=n.brush.vertices[f.vertices[0]],b=n.brush.vertices[f.vertices[1]],c=n.brush.vertices[f.vertices[2]];
    return csg::moveVertices(n.brush,f.vertices,csg::normalized(csg::cross(b-a,c-a))*distance,editErrors);
  });
  ImGui::SameLine();
  if (ImGui::Button("Extrude face"))
  {
    csg::Mesh prism;
    if (csg::extrudeFace(n.brush,faceIndex,distance,prism,editErrors))
    {
      csg::Node extra; extra.name="Extrusion"; extra.brush=std::move(prism); extra.transform=n.transform;
      if (distance<0) extra.operation=csg::Operation::Subtract;
      edit("Extrude CSG face",[&] {
        auto *parent=parentOf(document.root,n.id); if (!parent) return false;
        document.assignIds(extra); selected=extra.id; parent->children.push_back(std::move(extra)); return true;
      });
    }
  }
  if (ImGui::Button("Bevel selected edge / vertex")) edit("Bevel CSG components",[&] {
    csg::Id id=document.allocate();
    if (!csg::bevel(n.brush,components,distance,id,editErrors)) return false;
    n.brush.faces.back().sourceBrush=n.id; return true;
  });
  ImGui::InputFloat3("Clip normal",clipNormal); ImGui::InputFloat("Clip distance",&clipDistance);
  auto clipping=[&](bool split,bool invert) {
    edit(split ? "Split CSG brush":"Clip CSG brush",[&] {
      csg::Vec normal={clipNormal[0],clipNormal[1],clipNormal[2]};
      csg::Node other=n;
      if (!csg::clip(n.brush,normal*(invert ? -1:1),clipDistance*(invert ? -1:1),document.allocate(),n.brush.faces[faceIndex].surface,editErrors)) return false;
      n.brush.faces.back().sourceBrush=n.id;
      if (split)
      {
        if (!csg::clip(other.brush,normal*-1,-clipDistance,document.allocate(),other.brush.faces[faceIndex].surface,editErrors)) return false;
        document.assignIds(other); other.name+=" split";
        auto *parent=parentOf(document.root,n.id); if (!parent) return false; parent->children.push_back(std::move(other));
      }
      components.clear(); return true;
    });
  };
  if (ImGui::Button("Clip front")) clipping(false,false);
  ImGui::SameLine(); if (ImGui::Button("Clip back")) clipping(false,true);
  ImGui::SameLine(); if (ImGui::Button("Split")) clipping(true,false);
}
void BrushEditor::extrusionProperties(csg::Node &n)
{
  uint64_t key=csg::fingerprint(n);
  if(extrusionEditing!=n.id || extrusionFingerprint!=key) {
    extrusionEditing=n.id; extrusionFingerprint=key; extrusionDraft=n.extrusion;
    extrusionDraftSurfaces=n.extrusionSurfaces;
  }
  if(ImGui::RadioButton("Depth extrusion",extrusionDraft.mode==csg::ExtrusionMode::Depth)) extrusionDraft.mode=csg::ExtrusionMode::Depth;
  ImGui::SameLine(); if(ImGui::RadioButton("Spin extrusion",extrusionDraft.mode==csg::ExtrusionMode::Spin)) extrusionDraft.mode=csg::ExtrusionMode::Spin;
  ImGui::SameLine(); if(ImGui::RadioButton("Path extrusion",extrusionDraft.mode==csg::ExtrusionMode::Path)) {
    extrusionDraft.mode=csg::ExtrusionMode::Path;
    if(extrusionDraft.path.empty()) extrusionDraft.path={{{0,0,0},{},{0,0,-1}},{{0,0,-4},{0,0,1},{}}};
  }
  if(auto tree=TreeScope("Profile vertices")) {
    extrusionProfilePoint=std::clamp(extrusionProfilePoint,0,int(extrusionDraft.polygon.size())-1);
    ImGui::SliderInt("Profile vertex",&extrusionProfilePoint,0,int(extrusionDraft.polygon.size())-1);
    auto &p=extrusionDraft.polygon[extrusionProfilePoint]; double xy[]={p.x,p.y};
    if(ImGui::InputScalarN("Vertex XY",ImGuiDataType_Double,xy,2,nullptr,nullptr,"%.9g")) { p.x=xy[0]; p.y=xy[1]; }
    if(ImGui::Button("Insert vertex") && extrusionDraft.polygon.size()<256) {
      int next=extrusionProfilePoint+1; auto midpoint=(p+extrusionDraft.polygon[next%extrusionDraft.polygon.size()])*0.5;
      extrusionDraft.polygon.insert(extrusionDraft.polygon.begin()+next,midpoint);
      extrusionDraftSurfaces.insert(extrusionDraftSurfaces.begin()+next+2,0); extrusionProfilePoint=next;
      if(!extrusionDraft.surfaces.empty()) {
        auto inherited=extrusionDraft.surfaces[next+1];
        extrusionDraft.surfaces.insert(extrusionDraft.surfaces.begin()+next+2,inherited);
      }
    }
    ImGui::SameLine(); if(ImGui::Button("Remove vertex") && extrusionDraft.polygon.size()>3) {
      extrusionDraft.polygon.erase(extrusionDraft.polygon.begin()+extrusionProfilePoint);
      extrusionDraftSurfaces.erase(extrusionDraftSurfaces.begin()+extrusionProfilePoint+2);
      if(!extrusionDraft.surfaces.empty()) extrusionDraft.surfaces.erase(extrusionDraft.surfaces.begin()+extrusionProfilePoint+2);
    }
  }
  if(extrusionDraft.mode==csg::ExtrusionMode::Depth) inputDouble("Depth",extrusionDraft.depth);
  if(extrusionDraft.mode==csg::ExtrusionMode::Spin) {
    inputDouble("Spin degrees",extrusionDraft.spinDegrees);
    int sides=int(extrusionDraft.spinSides); ImGui::InputInt("Spin sides",&sides); extrusionDraft.spinSides=unsigned(sides);
  }
  if(extrusionDraft.mode==csg::ExtrusionMode::Path) {
    extrusionCurvePoint=std::clamp(extrusionCurvePoint,0,int(extrusionDraft.path.size())-1);
    ImGui::SliderInt("Curve point",&extrusionCurvePoint,0,int(extrusionDraft.path.size())-1);
    auto &p=extrusionDraft.path[extrusionCurvePoint]; inputVec("Curve position",p.position);
    if(auto tree=TreeScope("Bezier handles and tilt")) {
      ImGui::TextWrapped("Handles are offsets from the selected curve point.");
      inputVec("Incoming handle",p.incoming); inputVec("Outgoing handle",p.outgoing);
      double degrees=p.tilt*180/3.14159265358979323846;
      if(inputDouble("Tilt (degrees)",degrees,angleSnap)) p.tilt=degrees*3.14159265358979323846/180;
    }
    if(ImGui::Button("Add curve point") && extrusionDraft.path.size()<128) {
      auto last=extrusionDraft.path.back(); auto delta=last.position-extrusionDraft.path[extrusionDraft.path.size()-2].position;
      extrusionDraft.path.back().outgoing=delta/3;
      extrusionDraft.path.push_back({last.position+delta,delta*(-1.0/3),{},last.tilt}); extrusionCurvePoint=int(extrusionDraft.path.size())-1;
    }
    ImGui::SameLine(); if(ImGui::Button("Remove curve point") && extrusionDraft.path.size()>size_t(extrusionDraft.pathJoined ? 3:2))
      extrusionDraft.path.erase(extrusionDraft.path.begin()+extrusionCurvePoint);
    int divisions=int(extrusionDraft.pathSubdivisions); ImGui::InputInt("Path subdivisions",&divisions); extrusionDraft.pathSubdivisions=unsigned(divisions);
    ImGui::Checkbox("Join path ends",&extrusionDraft.pathJoined);
  }
  ImGui::TextWrapped("Apply validates the complete solid. Invalid changes retain the saved parameters and last valid geometry. Use the object gizmo for transforms.");
  if(ImGui::Button("Apply extrusion parameters")) edit("Edit parametric CSG extrusion",[&] {
    auto candidate=extrusionDraft;
    csg::Mesh generated; if(!csg::generateExtrusion(candidate,generated,editErrors)) return false;
    n.extrusion=std::move(candidate); n.extrusionSurfaces=extrusionDraftSurfaces;
    for(auto &id:n.extrusionSurfaces) if(!id) id=document.allocate();
    components.clear(); this->mode=0; return true;
  });
}
void BrushEditor::surfaces(csg::Node &n)
{
  if (!n.parametric && n.brush.faces.empty())
  {
    bool enabled=n.overrideCutSurface;
    if(ImGui::Checkbox("Override subtraction surface",&enabled)) edit("Override CSG group cut surface",[&] {
      n.overrideCutSurface=enabled; if(enabled && haveCopiedSurface) n.cutSurface=copiedSurface; return true;
    });
    ImGui::TextWrapped("Copy a brush face's surface, then apply it to this operation.");
    if(ImGui::Button("Use copied surface as cut override") && haveCopiedSurface)
      edit("Set CSG group cut surface",[&] { n.overrideCutSurface=true; n.cutSurface=copiedSurface; return true; });
    if(n.overrideCutSurface) ImGui::Text("Cut material: %s",n.cutSurface.material.empty() ? "Default":n.cutSurface.material.c_str());
    return;
  }
  if(n.closedMesh || n.parametric) ImGui::InputInt("Face index",&faceIndex);
  faceIndex=std::clamp(faceIndex,0,int(n.parametric ? n.extrusionSurfaces.size():n.brush.faces.size())-1);
  if(n.parametric) ImGui::TextWrapped("Surface 0: front cap; 1: back cap; 2 onward: profile edges. Surface IDs persist when parameters change.");
  auto &s=n.parametric ? (n.extrusion.surfaces.empty() ? n.extrusion.surface:n.extrusion.surfaces[faceIndex].surface):n.brush.faces[faceIndex].surface;
  csg::Surface proposed=s;
  bool automaticUv=n.parametric && (n.extrusion.surfaces.empty() || n.extrusion.surfaces[faceIndex].automaticUv);
  auto apply=[&](const csg::Surface &value,bool automatic) {
    if(n.parametric) {
      if(n.extrusion.surfaces.empty()) n.extrusion.surfaces.resize(n.extrusion.polygon.size()+2,{n.extrusion.surface,true});
      n.extrusion.surfaces[faceIndex]={value,automatic};
    } else n.brush.faces[faceIndex].surface=value;
  };
  char material[512]; std::snprintf(material,sizeof(material),"%s",s.material.c_str());
  bool changed=ImGui::InputText("Material asset",material,sizeof(material),ImGuiInputTextFlags_EnterReturnsTrue);
  if(changed) proposed.material=material;
  ImGui::TextDisabled("Press Enter to apply the material asset.");
  changed|=inputDouble("U scale",proposed.scaleU); changed|=inputDouble("V scale",proposed.scaleV);
  changed|=inputDouble("U offset",proposed.offsetU); changed|=inputDouble("V offset",proposed.offsetV);
  changed|=inputDouble("UV rotation",proposed.rotation); changed|=ImGui::Checkbox("World locked",&proposed.worldLocked);
  if(n.parametric) changed|=ImGui::Checkbox("Follow extrusion UVs",&automaticUv);
  if(!n.parametric || !automaticUv) { changed|=inputVec("U mapping axis",proposed.u); changed|=inputVec("V mapping axis",proposed.v); }
  int smoothing=int(proposed.smoothing); changed|=ImGui::InputInt("Smoothing mask (0 = hard)",&smoothing); proposed.smoothing=uint32_t(smoothing);
  if (changed) edit("Edit CSG surface",[&] { apply(proposed,automaticUv); csg::Mesh mesh; return n.parametric ? csg::generateExtrusion(n.extrusion,mesh,editErrors):csg::validate(n.brush,editErrors,n.id,!n.closedMesh); });
  csg::Transform world;
  std::function<bool(const csg::Node &,const csg::Transform &)> findWorld;
  findWorld=[&](const csg::Node &node,const csg::Transform &parent) {
    auto tm=compose(parent,node.transform);
    if(node.id==n.id) { world=tm; return true; }
    for(const auto &child:node.children) if(findWorld(child,tm)) return true;
    return false;
  }; findWorld(document.root,{});
  if (ImGui::Button("Copy mapping")) {
    copiedSurface=csg::transformedSurface(s,world);
    if(n.parametric) {
      csg::Mesh generated; csg::Diagnostics errors;
      if(csg::generateExtrusion(n.extrusion,generated,errors))
        for(const auto &face:generated.faces) if(face.id==csg::Id(faceIndex+1)) {
          copiedSurface=csg::transformedSurface(face.surface,world); break;
        }
    }
    // Copied axes are now in world space, including for operation overrides.
    // Alignment converts them back to local axes for brush-locked targets.
    copiedSurface.worldLocked=true; haveCopiedSurface=true;
  }
  ImGui::SameLine(); if (ImGui::Button("Align to copied mapping") && haveCopiedSurface)
    edit("Align CSG mapping",[&] {
      auto mapping=copiedSurface;
      if(!s.worldLocked) {
        csg::Transform inverse; inverse.column[3]=world.inversePoint({});
        for(int i=0;i<3;++i) { csg::Vec axis{}; if(i==0) axis.x=1; else if(i==1) axis.y=1; else axis.z=1;
          inverse.column[i]=world.inversePoint(axis)-inverse.column[3]; }
        mapping.worldLocked=false; mapping=csg::transformedSurface(mapping,inverse);
      }
      mapping.worldLocked=s.worldLocked;
      auto aligned=s; csg::alignSurface(aligned,mapping); apply(aligned,false); return true;
    });
  if (ImGui::Button("Apply surface to brush")) edit("Apply CSG surface",[&] {
    if(n.parametric) { auto value=s; n.extrusion.surface=value; n.extrusion.surfaces.assign(n.extrusion.polygon.size()+2,{value,automaticUv}); }
    else for (auto &f:n.brush.faces) f.surface=s;
    return true;
  });
  ImGui::InputText("Replace material",replaceFrom,sizeof(replaceFrom)); ImGui::InputText("With material",replaceTo,sizeof(replaceTo));
  if (ImGui::Button("Replace throughout model")) edit("Replace CSG material",[&] {
    std::function<void(csg::Node &)> replace=[&](csg::Node &node) {
      for (auto &f:node.brush.faces) if (f.surface.material==replaceFrom) f.surface.material=replaceTo;
      if(node.parametric && node.extrusion.surface.material==replaceFrom) node.extrusion.surface.material=replaceTo;
      for(auto &face:node.extrusion.surfaces) if(face.surface.material==replaceFrom) face.surface.material=replaceTo;
      if(node.overrideCutSurface && node.cutSurface.material==replaceFrom) node.cutSurface.material=replaceTo;
      for (auto &c:node.children) replace(c);
    }; replace(document.root); return true;
  });
  bool overrideCut=n.overrideCutSurface;
  if (ImGui::Checkbox("Override subtraction surface",&overrideCut)) edit("Override CSG cut surface",[&] {
    n.overrideCutSurface=overrideCut; n.cutSurface=s; return true;
  });
  if (n.overrideCutSurface && ImGui::Button("Use selected face as cut override"))
    edit("Set CSG cut surface",[&] { n.cutSurface=s; return true; });
}
void BrushEditor::updateImgui()
{
  if (!visible) return;
  ImGui::SetNextWindowSize(ImVec2(520,640),ImGuiCond_FirstUseEver);
  auto window=IDaEditor3Engine::ScopedImguiWindow("CSG Brushes",&visible);
  if (!window.canSubmitContents()) return;
  try { drawContents(); } catch (const UiEditFinished &) {}
}
void BrushEditor::drawContents()
{
  if(dgs_get_settings()->getBlockByNameEx("debug")->getStr("editorUiTest",nullptr))
  {
    String state(128,"Test source %llu valid %d atlas %d sample %.9g",csg::fingerprint(document.root),int(current.success),lightmapSize,lightmapSampleSize);
    ImGui::Button(state.c_str());
  }
  if(benchmarkFrame>=0) { ImGui::Text("Full-pipeline benchmark frame %d / 13",benchmarkFrame); return; }
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgBenchmark",false) &&
    ImGui::Button("Run CSG release benchmark")) { startBenchmark(); return; }
  ImGui::TextWrapped("Create convex brushes, combine them in the hierarchy, then edit components and surfaces.");
  ImGui::TextWrapped("CSG exports as editable entities automatically. F2 transforms update rendering and collision together.");
  if(ImGui::IsItemHovered()) ImGui::SetTooltip("Export editable source instead of baked CSG. The engine owns rendering and collision updates for runtime cuts.");
  if (loadFailed)
  {
    ImGui::TextColored(ImVec4(1,0.2f,0.2f,1),"Document load failed. Original data retained; export blocked.");
    for (const auto &error:editErrors)
      ImGui::TextWrapped("Node %llu, face %llu: %s",error.node,error.face,error.message.c_str());
    return;
  }
  ImGui::Text("Update: %.3f ms | Carve calls: %zu | Cache hits: %zu",updateMs,current.booleanCalls,current.cacheHits);
  if (!current.success) ImGui::TextColored(ImVec4(1,0.3f,0.2f,1),"STALE PREVIEW - export blocked");
  for (const auto &e:current.diagnostics) ImGui::TextWrapped("Node %llu, face %llu: %s",e.node,e.face,e.message.c_str());
  for (const auto &e:editErrors) ImGui::TextWrapped("Edit rejected: %s",e.message.c_str());
  if (ImGui::CollapsingHeader("Create",ImGuiTreeNodeFlags_DefaultOpen))
  {
    ImGui::TextWrapped("Add a shape, choose Union / Subtract / Intersect, then use daEditor's move, rotate and scale gizmos.");
    ImGui::InputFloat3("Dimensions",size); ImGui::InputInt("Sides / segments",&cylinderSides);
    if (shapeButton("Box","create_box","Create a convex box. Use the native move, rotate and scale gizmos.")) add(csg::box({size[0],size[1],size[2]}),"Box");
    ImGui::SameLine(); if (shapeButton("Ramp","create_box","Create a convex ramp.")) add(csg::ramp({size[0],size[1],size[2]}),"Ramp");
    ImGui::SameLine(); if (shapeButton("Cylinder","create_cylinder","Create a cylinder using the dimensions and side count above.")) add(csg::cylinder(size[0]*0.5,size[1],cylinderSides),"Cylinder");
    auto nativeSphere=[&] {
      StaticGeometryContainer source;
      auto *library=EDITORCORE->queryEditorInterface<IEditorPrimitiveGeometry>();
      bool ok=library && library->generate(IEditorPrimitiveGeometry::Sphere,cylinderSides,source);
      if(!ok) { editErrors={{csg::Code::InvalidMesh,0,0,"Dagor could not create the primitive"}}; return; }
      for(auto *node:source.nodes) {
        node->wtm.setcol(0,Point3(size[0],0,0)); node->wtm.setcol(1,Point3(0,size[1],0)); node->wtm.setcol(2,Point3(0,0,size[2]));
      }
      addNativeGeometry(source,"Sphere");
    };
    if(shapeButton("Sphere","create_sphere","Create a sphere with Dagor's existing primitive builder.")) nativeSphere();
    ImGui::SameLine(); if(shapeButton("Capsule","contour_capsule","Spin preset. X is diameter and Y is total height; increase height for a straight middle.")) {
      csg::Extrusion shape; shape.mode=csg::ExtrusionMode::Spin; shape.spinSides=unsigned(cylinderSides);
      double radius=size[0]*0.5,halfBody=size[1]*0.5-radius;
      if(!std::isfinite(radius)||!std::isfinite(halfBody)||radius<=0||halfBody<0) editErrors={{csg::Code::InvalidMesh,0,0,"Capsule requires height >= diameter > 0"}};
      else {
        int steps=16;
        for(int i=0;i<=steps;++i) {
          double a=3.14159265358979323846*i/steps;
          double x=(i==0 || i==steps) ? 0:radius*std::sin(a),y=radius*std::cos(a);
          if(i==steps/2) { shape.polygon.push_back({radius,halfBody,0}); if(halfBody>0) shape.polygon.push_back({radius,-halfBody,0}); }
          else shape.polygon.push_back({x,y+(i<steps/2 ? halfBody:-halfBody),0});
        }
        addExtrusion(std::move(shape),"Capsule");
      }
    }
    ImGui::SameLine(); if(shapeButton("Mesh...","import_dag","Import closed DAG geometry through Dagor's existing loader. Uses the CSG default material; keeps UVs and smoothing.")) importClosedMesh();
    static float majorRadius=2,minorRadius=0.5f;
    ImGui::InputFloat("Torus major radius",&majorRadius); ImGui::InputFloat("Torus tube radius",&minorRadius);
    if(shapeButton("Torus","create_cylinder","Create a torus as an editable spin extrusion. Reuses the same validated polygon sweep.")) {
      if(!std::isfinite(majorRadius)||!std::isfinite(minorRadius)||minorRadius<=0||majorRadius<=minorRadius) {
        editErrors.push_back({csg::Code::InvalidMesh,0,0,"Torus requires major radius > tube radius > 0"}); return;
      }
      csg::Extrusion shape; shape.mode=csg::ExtrusionMode::Spin; shape.spinSides=unsigned(cylinderSides);
      for(int i=0;i<16;++i) { double a=2*3.14159265358979323846*i/16; shape.polygon.push_back({majorRadius+minorRadius*std::cos(a),minorRadius*std::sin(a),0}); }
      addExtrusion(std::move(shape),"Torus");
    }
    if (ImGui::Button("Operation group")) edit("Create CSG group",[&] {
      auto *parent=document.find(selected); if (!parent || parent->parametric || !parent->brush.faces.empty()) parent=&document.root;
      csg::Node group; group.name="Group"; document.assignIds(group); selected=group.id; parent->children.push_back(std::move(group)); return true;
    });
    if(ImGui::Button("Parametric polygon")) {
      csg::Extrusion shape; shape.polygon={{0,0,0},{2,0,0},{2,2,0},{0,2,0}};
      shape.path={{{0,0,0},{},{0,0,-1}},{{0,0,-4},{0,0,1},{}}}; addExtrusion(std::move(shape),"Polygon extrusion");
    }
    if(auto tree=TreeScope("Outline extrusion")) {
    ImGui::InputTextMultiline("Outline XYZ",outline,sizeof(outline),ImVec2(-1,100)); ImGui::InputFloat3("Extrude vector",extrusion);
    if (ImGui::Button("Extrude outline"))
    {
      std::istringstream stream(outline); stream.imbue(std::locale::classic()); std::vector<csg::Vec> points;
      csg::Vec p; bool incomplete=false;
      while (true) { stream>>std::ws; if (stream.eof()) break;
        if (!(stream>>p.x>>p.y>>p.z)) { incomplete=true; break; } points.push_back(p); }
      std::vector<csg::Mesh> prisms; editErrors.clear();
      if (incomplete) editErrors.push_back({csg::Code::InvalidMesh,0,0,"Outline must contain XYZ triples"});
      else if (csg::extrudeOutline(points,{extrusion[0],extrusion[1],extrusion[2]},prisms,editErrors))
        edit("Extrude CSG outline",[&] {
          csg::Node group; group.name="Outline extrusion";
          for (auto &mesh:prisms) { csg::Node brush; brush.name="Convex prism"; brush.brush=std::move(mesh); group.children.push_back(std::move(brush)); }
          document.assignIds(group); selected=group.id; document.root.children.push_back(std::move(group)); return true;
        });
    }
  }
  }
  if (ImGui::CollapsingHeader("Hierarchy",ImGuiTreeNodeFlags_DefaultOpen)) hierarchy(document.root);
  if (pendingMove)
  {
    auto moved=pendingMove,target=pendingParent; pendingMove=0;
    edit("Reparent CSG node",[&] {
      auto *node=document.find(moved),*parent=parentOf(document.root,moved);
      if (!node || !parent) return false;
      csg::Document branch; branch.root=*node; if (branch.find(target)) return false;
      csg::Node copy=*node;
      parent->children.erase(std::remove_if(parent->children.begin(),parent->children.end(),[&](const csg::Node &c){return c.id==moved;}),parent->children.end());
      auto *dest=document.find(target); if (!dest || !dest->brush.faces.empty()) return false; dest->children.push_back(std::move(copy)); return true;
    });
  }
  auto *n=document.find(selected); if (!n) { selected=document.root.id; n=&document.root; }
  char name[256]; std::snprintf(name,sizeof(name),"%s",n->name.c_str());
  if (ImGui::InputText("Name",name,sizeof(name),ImGuiInputTextFlags_EnterReturnsTrue)) edit("Rename CSG node",[&]{n->name=name;return true;});
  bool enabled=n->visible;
  if (ImGui::Checkbox("Enabled",&enabled)) edit("Enable CSG node",[&]{n->visible=enabled;return true;});
  int op=int(n->operation);
  if (ImGui::Combo("Operation",&op,"Union\0Subtract\0Intersect\0")) edit("Set CSG operation",[&]{n->operation=csg::Operation(op);return true;});
  inputDouble("Grid spacing",grid); inputDouble("Angle snap (degrees)",angleSnap);
  csg::Transform transform=n->transform; bool changed=inputVec("Position",transform.column[3]);
  if(auto tree=TreeScope("Advanced transform axes")) {
    changed|=inputVec("X axis",transform.column[0]); changed|=inputVec("Y axis",transform.column[1]); changed|=inputVec("Z axis",transform.column[2]);
  }
  if (changed) edit("Transform CSG node",[&] {
    if (grid>0) { auto &p=transform.column[3]; p.x=std::round(p.x/grid)*grid; p.y=std::round(p.y/grid)*grid; p.z=std::round(p.z/grid)*grid; }
    if (!std::isfinite(transform.determinant()) || std::abs(transform.determinant())<1e-12) return false;
    n->transform=transform; return true;
  });
  if (n->id!=document.root.id)
  {
    if (ImGui::Button("Duplicate node")) { duplicateSelection(); return; }
    ImGui::SameLine();
    if (ImGui::Button("Delete node")) { auto id=n->id; edit("Delete CSG node",[&] {
      auto *parent=parentOf(document.root,id); if (!parent) return false;
      parent->children.erase(std::remove_if(parent->children.begin(),parent->children.end(),[&](const csg::Node &c){return c.id==id;}),parent->children.end());
      selected=parent->id; return true;
    }); return; }
    ImGui::SameLine();
    auto reorder=[&](int delta) { edit("Reorder CSG operation",[&] {
      auto *parent=parentOf(document.root,n->id); if (!parent) return false;
      for (size_t i=0;i<parent->children.size();++i) if (parent->children[i].id==n->id)
      { int target=int(i)+delta; if (target<0 || target>=int(parent->children.size())) return false;
        std::swap(parent->children[i],parent->children[target]); return true; } return false;
    }); };
    if (ImGui::Button("Earlier")) { reorder(-1); return; } ImGui::SameLine(); if (ImGui::Button("Later")) { reorder(1); return; }
    if(auto tree=TreeScope("Repeat duplication")) {
    ImGui::InputInt("Copies",&repeatCount); ImGui::InputFloat3("Translation increment",increment);
    ImGui::InputFloat3("Rotation increment",repeatRotation); ImGui::InputFloat3("Scale increment",repeatScale);
    if (ImGui::Button("Repeat duplicate"))
    {
      csg::Node source=*n;
      edit("Repeat CSG duplicate",[&] {
        if (repeatCount<1 || repeatCount>10000) return false;
        auto *parent=parentOf(document.root,source.id); if (!parent) return false;
        csg::Transform step;
        step.column[3]={increment[0],increment[1],increment[2]};
        auto snapPosition=[&](csg::Vec &p) {
          if(grid>0) { p.x=std::round(p.x/grid)*grid; p.y=std::round(p.y/grid)*grid; p.z=std::round(p.z/grid)*grid; }
        };
        snapPosition(step.column[3]);
        for (unsigned axis=0;axis<3;++axis)
        {
          double degrees=repeatRotation[axis]; if (angleSnap>0) degrees=std::round(degrees/angleSnap)*angleSnap;
          double angle=degrees*3.14159265358979323846/180; csg::Transform rotation;
          unsigned u=(axis+1)%3,v=(axis+2)%3;
          double *cu=&rotation.column[u].x,*cv=&rotation.column[v].x;
          cu[u]=std::cos(angle); cu[v]=std::sin(angle); cv[u]=-std::sin(angle); cv[v]=std::cos(angle);
          for (unsigned i=0;i<3;++i) step.column[i]=rotation.vector(step.column[i]);
        }
        for (unsigned i=0;i<3;++i) step.column[i]=step.column[i]*repeatScale[i];
        for (int i=0;i<repeatCount;++i)
        {
          source.transform=compose(step,source.transform); snapPosition(source.transform.column[3]);
          auto copy=source; document.assignIds(copy); copy.name+=" copy";
          parent->children.push_back(std::move(copy));
        }
        return true;
      }); return;
    }
  }
  }
  if (ImGui::CollapsingHeader("Component modelling",ImGuiTreeNodeFlags_DefaultOpen)) { modelling(*n); if (dirty) return; }
  if (ImGui::CollapsingHeader("Surface mapping")) surfaces(*n);
  if (ImGui::CollapsingHeader("Lightmap UV preparation"))
  {
    int lm=lightmapSize; float sample=lightmapSampleSize;
    if (ImGui::InputInt("Atlas size",&lm) && lm>=32 && lm<=2048 && (lm&(lm-1))==0)
      edit("Change CSG lightmap atlas size",[&] { lightmapSize=lm; return true; });
    if (ImGui::InputFloat("Sample size",&sample) && std::isfinite(sample) && sample>0)
      edit("Change CSG lightmap sample size",[&] { lightmapSampleSize=sample; return true; });
    ImGui::TextWrapped("Scene-builder defaults: 1024 atlas, 0.1 m sample. Per-CSG overrides use Dagor's existing chart padding. Supported atlas sizes: 32 to 2048. No lighting bake is performed.");
  }
}

MaterialData *BrushEditor::resolveMaterial(const std::string &name,csg::Id brush,csg::Id face)
{
  auto *assets=EDITORCORE->queryEditorInterface<IAssetService>();
  if(!name.empty()) {
    auto *material=assets ? assets->getMaterialData(name.c_str()):nullptr;
    if(!material) current.diagnostics.push_back({csg::Code::InvalidResult,brush,face,"Cannot resolve material asset: "+name});
    return material;
  }
  DataBlock application(DAGORED2->getWorkspace().getAppBlkPath());
  bool dng=application.getBlockByNameEx("game")->getBool("daNetGameEditorRender",false);
  if(dng && (defaultTexture.empty() || defaultNormalTexture.empty())) {
    current.diagnostics.push_back({csg::Code::InvalidResult,brush,face,
      "Set brushEditorSettings/defaultTexture and defaultNormalTexture to project texture assets, or assign a static material asset"});
    return nullptr;
  }
  auto *data=new MaterialData; data->className=dng ? "csg_static":"simple";
  data->mat.diff=Color4(0.7f,0.7f,0.7f,1); data->mat.power=0;
  data->mtex[0]=dagRender->addManagedTexture(defaultTexture.empty() ?
    editorcore_extapi::make_full_start_path("../commonData/tex/missing.dds"):defaultTexture.c_str());
  if(dng) data->mtex[2]=dagRender->addManagedTexture(defaultNormalTexture.c_str());
  return data;
}
std::map<std::string,Ptr<MaterialData>> BrushEditor::runtimePalette()
{
  std::set<std::string> names={""};
  std::function<void(const csg::Node &)> visit=[&](const csg::Node &node) {
    for(const auto &face:node.brush.faces) names.insert(face.surface.material);
    if(node.parametric) names.insert(node.extrusion.surface.material);
    for(const auto &face:node.extrusion.surfaces) names.insert(face.surface.material);
    if(node.overrideCutSurface) names.insert(node.cutSurface.material);
    for(const auto &child:node.children) visit(child);
  }; visit(document.root);
  std::map<std::string,Ptr<MaterialData>> palette;
  for(const auto &name:names) {
    auto *data=resolveMaterial(name); if(!data) return {};
    palette[name]=data;
  }
  return palette;
}
bool BrushEditor::collectRuntimeTextures(ITextureNumerator &textures)
{
  if(document.root.children.empty()) return true;
  auto palette=runtimePalette(); if(palette.empty()) return false;
  for(const auto &[name,data]:palette) for(auto texture:data->mtex)
    if(texture!=BAD_TEXTUREID && textures.addManagedTexture(texture)<0) return false;
  return true;
}
bool BrushEditor::writeRuntimeSettings(DataBlock &source,const ITextureNumerator &textures)
{
  source.setBool("runtimeEditable",true);
  auto palette=runtimePalette(); if(palette.empty()) return false;
  source.setInt("lightmapSize",lightmapSize); source.setReal("lightmapSampleSize",lightmapSampleSize);
  auto &out=*source.addNewBlock("runtimeMaterials");
  for(const auto &[name,data]:palette) {
    auto &material=*out.addNewBlock("material");
    material.setStr("name",name.c_str()); material.setStr("class",data->className);
    material.setStr("script",data->matScript); material.setInt("flags",data->flags);
    auto color=[&](const char *key,Color4 c) { material.setPoint4(key,Point4(c.r,c.g,c.b,c.a)); };
    color("diffuse",data->mat.diff); color("ambient",data->mat.amb); color("specular",data->mat.spec); color("emissive",data->mat.emis);
    material.setReal("power",data->mat.power);
    for(int slot=0;slot<MAXMATTEXNUM;++slot) if(data->mtex[slot]!=BAD_TEXTUREID) {
      int ordinal=textures.getManagedTextureOrdinal(data->mtex[slot]); if(ordinal<0) return false;
      auto &texture=*material.addNewBlock("texture"); texture.setInt("slot",slot); texture.setInt("ordinal",ordinal);
    }
  }
  return true;
}
bool BrushEditor::buildPublished(const csg::Mesh &polygons,StaticGeometryContainer &container)
{
  csg::Mesh source;
  csg::Vec origin;
  if(!csg::prepareFloatPublication(polygons,source,origin,current.diagnostics))
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Triangulation did not produce a valid publication mesh"}); return false; }
  if (source.faces.empty()) return true;
  auto *mesh=new Mesh;
  mesh->vert.resize(source.vertices.size());
  for (size_t i=0;i<source.vertices.size();++i) mesh->vert[i]=point(source.vertices[i]);
  // Verify the actual float publication does not collapse valid geometry.
  csg::Mesh converted=source;
  for (size_t i=0;i<source.vertices.size();++i) converted.vertices[i]=vec(mesh->vert[i]);
  if (!csg::validate(converted,current.diagnostics))
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Float publication collapsed geometry"}); delete mesh; return false; }
  MaterialDataList materials;
  std::map<std::string,int> materialIds;
  for (const auto &face:source.faces)
  {
    int mat=0; auto found=materialIds.find(face.surface.material);
    if (found==materialIds.end())
    {
      MaterialData *data=resolveMaterial(face.surface.material,face.sourceBrush,face.id);
      if(!data) { delete mesh; return false; }
      mat=materials.addSubMat(data); materialIds[face.surface.material]=mat;
    }
    else mat=found->second;
    for (size_t i=1;i+1<face.vertices.size();++i)
    {
      Face triangle{}; triangle.v[0]=face.vertices[0]; triangle.v[1]=face.vertices[i]; triangle.v[2]=face.vertices[i+1];
      triangle.mat=mat; triangle.smgr=face.surface.smoothing; mesh->face.push_back(triangle);
      TFace tex{};
      for (unsigned j=0;j<3;++j)
      {
      auto uv=csg::textureCoordinates(face.surface,source.vertices[triangle.v[j]]+origin);
        tex.t[j]=mesh->tvert[0].size(); mesh->tvert[0].push_back(Point2(float(uv[0]),float(uv[1])));
      }
      mesh->tface[0].push_back(tex);
    }
  }
  if (lightmapSize<32 || lightmapSize>2048 || (lightmapSize&(lightmapSize-1)) ||
      !std::isfinite(lightmapSampleSize) || lightmapSampleSize<=0)
  {
    current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Invalid lightmap settings"}); delete mesh; return false;
  }
  // AutoUnwrapMapping is a global session. Never run it concurrently or retain
  // its returned pointer beyond finish_mapping().
  static bool mappingParityChecked=false;
  if(!mappingParityChecked && dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgMappingParity",false))
  {
    for(float scale:{1.0f,0.75f})
      if(!mappingEqual(mappingSnapshot(*mesh,lightmapSize,lightmapSampleSize,false,scale),
                       mappingSnapshot(*mesh,lightmapSize,lightmapSampleSize,true,scale)))
      { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Disk/memory UV parity failed"}); delete mesh; return false; }
    mappingParityChecked=true; DAEDITOR3.conNote("CSG disk/memory UV parity PASS (including repeated atlas packing)");
  }
  struct MappingScope
  { MappingScope(int size) { AutoUnwrapMapping::start_mapping_in_memory(size); } ~MappingScope() { AutoUnwrapMapping::finish_mapping(); } } mapping(lightmapSize);
  QuietProgressIndicator progress; SimpleProgressCB cancel;
  int handle=AutoUnwrapMapping::request_mapping(mesh->face.data(),mesh->face.size(),mesh->vert.data(),mesh->vert.size(),
    lightmapSampleSize,false,AutoUnwrapMapping::SCHEME_DAGOR);
  AutoUnwrapMapping::prepare_facegroups(progress,cancel);
  int atlases=AutoUnwrapMapping::repack_facegroups(1,nullptr,0,progress,cancel);
  if (atlases<=0 || cancel.mustStop || handle<0)
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Lightmap UV generation failed"}); delete mesh; return false; }
  std::vector<unsigned short> pages(mesh->face.size());
  mesh->tface[1].resize(mesh->face.size()); Point2 *uv=nullptr; int count=0;
  AutoUnwrapMapping::get_final_mapping(handle,pages.data(),sizeof(unsigned short),mesh->tface[1].data(),uv,count);
  if (!uv || count<=0)
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"No lightmap coordinates generated"}); delete mesh; return false; }
  mesh->tvert[1].resize(count); for (int i=0;i<count;++i) mesh->tvert[1][i]=uv[i];
  // Bake authored hard edges before satisfying the legacy scene exporter's
  // nonzero-smoothing-mask requirement. Preserve the explicit normal groups
  // rather than allowing that compatibility mask to smooth hard boundaries.
  mesh->calc_ngr(); mesh->calc_vertnorms();
  // Preserve the renderer's front-face convention, but publish the authoring
  // solid's outward normals. Dagor's computed normals use the reverse cross
  // product from Carve's outward CCW faces.
  for(auto &normal:mesh->vertnorm) normal=-normal;
  for(auto &face:mesh->face) if(!face.smgr) face.smgr=1u<<30;
  // Separate nodes per atlas retain atlas ownership without overlapping charts
  // in a single lightmap UV domain. Geometry vertices retain component identity.
  for (int page=0;page<atlases;++page)
  {
    auto *pageMesh=new Mesh(*mesh);
    for (int i=pageMesh->face.size()-1;i>=0;--i)
      if (pages[i]!=page) pageMesh->removeFacesFast(i,1);
    if (pageMesh->face.empty()) { delete pageMesh; continue; }
    StaticGeometryContainer temporary;
    String name(64,"csg_brushes_lm_%d",page);
    if (!dagGeom->objCreator3dAddNode(name,pageMesh,&materials,temporary) || temporary.nodes.empty())
    { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Cannot create CSG geometry node"}); delete mesh; return false; }
    auto *node=temporary.nodes[0]; node->wtm.setcol(3,point(origin));
    node->flags|=StaticGeometryNode::FLG_COLLIDABLE|StaticGeometryNode::FLG_CASTSHADOWS;
    node->flags|=StaticGeometryNode::FLG_NO_RECOMPUTE_NORMALS;
    node->script.setBool("csgBrushGenerated",true); node->script.setInt("csgLightmapPage",page);
    dagGeom->staticGeometryNodeCalcBoundBox(*node); dagGeom->staticGeometryNodeCalcBoundSphere(*node);
    container.addNode(dagGeom->newStaticGeometryNode(*node));
  }
  delete mesh;
  return true;
}
void BrushEditor::update()
{
  auto start=std::chrono::steady_clock::now();
  syncGizmo();
  if (!dirty || loadFailed) return;
  OnExit reportFailure{[&] {
    if(current.success) return;
    for(const auto &error:current.diagnostics)
      DAEDITOR3.conError("CSG evaluation node %llu face %llu: %s",error.node,error.face,error.message.c_str());
    if(benchmarkFrame<0) return;
    DAEDITOR3.conError("CSG full-pipeline fixture FAILED at frame %d, neighbors=%d",benchmarkFrame,benchmarkNeighbors);
    document=std::move(*benchmarkSource); benchmarkSource.reset(); benchmarkFrame=-1; dirty=true;
  }};
  current=evaluator.evaluate(document); dirty=false;
  auto evaluatedAt=std::chrono::steady_clock::now();
  if (!current.success) return;
  std::vector<csg::ResultChunk> outputComponents=current.chunks;
  std::map<uint64_t,PublishedPart> nextParts;
  auto partitionedAt=std::chrono::steady_clock::now();
  double mappingMs=0,renderCollisionMs=0,joltMs=0;
  auto container=std::make_unique<StaticGeometryContainer>();
  auto discardNew=[&] {
    for(auto &part:nextParts) if(!parts.count(part.first) && part.second.geometry) dagGeom->deleteGeomObject(part.second.geometry);
  };
  csg::Node settingsKey; settingsKey.transform.column[3]={double(lightmapSize),lightmapSampleSize,0};
  uint64_t settingsHash=csg::fingerprint(settingsKey);
  for(const auto &component:outputComponents)
  {
    uint64_t hash=component.hash;
    hash^=settingsHash+0x9e3779b97f4a7c15ULL+(hash<<6)+(hash>>2);
    PublishedPart part;
    auto previous=parts.find(hash);
    if(previous!=parts.end()) part=previous->second;
    else
    {
      part.container=std::make_shared<StaticGeometryContainer>();
      auto mapStart=std::chrono::steady_clock::now();
      if(!buildPublished(*component.mesh,*part.container)) { discardNew(); current.success=false; return; }
      mappingMs+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-mapStart).count();
      auto compileStart=std::chrono::steady_clock::now();
      part.geometry=dagGeom->newGeomObject();
      dagGeom->geomObjectCreateFromGeomContainer(*part.geometry,*part.container);
      if(!part.container->nodes.empty() && !dagGeom->geomObjectReloadCollision(*part.geometry))
      {
        dagGeom->deleteGeomObject(part.geometry); discardNew(); current.success=false;
        current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Collision rebuild failed"}); return;
      }
      renderCollisionMs+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-compileStart).count();
      if(auto *physics=EDITORCORE->queryEditorInterface<ICsgCollisionPreparation>())
      {
        auto cookStart=std::chrono::steady_clock::now();
        void *shape=physics->prepare(*part.container);
        if(!shape)
        {
          dagGeom->deleteGeomObject(part.geometry); discardNew(); current.success=false;
          current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Jolt collision preparation failed"}); return;
        }
        part.physics=std::shared_ptr<void>(shape,[physics](void *p){physics->release(p);});
        joltMs+=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-cookStart).count();
      }
    }
    nextParts.emplace(hash,part);
    for(auto *node:part.container->nodes)
    {
      auto *copy=dagGeom->newStaticGeometryNode(*node);
      copy->name=String(96,"csg_%llu_%s",hash,node->name.str()); container->addNode(copy);
    }
  }
  // Commit every changed component together; failures leave the previous
  // render, UV and collision revision intact. Unchanged components retain all
  // derived outputs, including their independent atlas domains.
  for(auto &part:parts) if(!nextParts.count(part.first)) dagGeom->deleteGeomObject(part.second.geometry);
  parts=std::move(nextParts);
  delete published; published=container.release();
  updateMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
  if(acceptanceQueued)
  {
    acceptanceQueued=false; runAcceptance();
    if(benchmarkQueued) { benchmarkQueued=false; startBenchmark(); }
    return;
  }
  if(benchmarkFrame>=0)
  {
    DAEDITOR3.conNote("CSG publication partition %.3f ms, mapping %.3f ms, render+collision %.3f ms, Jolt cook %.3f ms",
      std::chrono::duration<double,std::milli>(partitionedAt-evaluatedAt).count(),mappingMs,renderCollisionMs,joltMs);
    DAEDITOR3.conNote("CSG stage evaluation %.3f ms, remaining publication %.3f ms, calls=%zu faces=%zu",
      std::chrono::duration<double,std::milli>(evaluatedAt-start).count(),
      std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-evaluatedAt).count(),
      current.booleanCalls,current.mesh->faces.size());
    if(benchmarkFrame>=3) benchmarkWorst=std::max(benchmarkWorst,updateMs);
    DAEDITOR3.conNote("CSG full-pipeline frame %d: %.3f ms (warmup=%d)",benchmarkFrame,updateMs,benchmarkFrame<3);
    if(++benchmarkFrame==13)
    {
      DAEDITOR3.conNote("CSG full-pipeline fixture neighbors=%d worst %.3f ms; timing %s (authoring acceptance separate)",benchmarkNeighbors,benchmarkWorst,benchmarkWorst<=33 ? "PASS":"FAIL");
      document=std::move(*benchmarkSource); benchmarkSource.reset(); benchmarkFrame=-1; dirty=true;
    }
    else { document.find(benchmarkEdited)->transform.column[3].y=benchmarkFrame*0.01; dirty=true; }
  }
}
void BrushEditor::runAcceptance()
{
  const auto source=document;
  const bool wasVisible=visible; visible=true;
  OnExit restoreSource{[&] { visible=wasVisible; restore(source); }};
  auto require=[](bool ok,const char *message) { if(!ok) throw std::runtime_error(message); };
  try
  {
    runLegacyCSGAcceptance();
    DAEDITOR3.conNote("CSG legacy generation backend acceptance PASS: building shell, non-convex closed-prefab cut, topology, volume, materials, UVs and smoothing");
    auto publishBrushes=[&](std::vector<csg::Mesh> brushes,const char *label) {
      csg::Document test; test.root.name=label; test.assignIds(test.root);
      for(auto &mesh:brushes) { csg::Node node; node.name=label; node.brush=std::move(mesh); test.assignIds(node); test.root.children.push_back(std::move(node)); }
      restore(std::move(test)); update(); require(current.success,label);
    };
    csg::Diagnostics modellingErrors;
    auto cube=csg::box({2,2,2});
    publishBrushes({cube},"box publication");
    require(published && !published->nodes.empty(),"Box has no published geometry");
    for(const auto *node:published->nodes)
    {
      const auto &mesh=node->mesh->mesh;
      require(mesh.facengr.size()==mesh.face.size(),"Published normal groups missing");
      for(int fi=0;fi<mesh.face.size();++fi)
      {
        const auto &face=mesh.face[fi];
        auto a=node->wtm*mesh.vert[face.v[0]],b=node->wtm*mesh.vert[face.v[1]],c=node->wtm*mesh.vert[face.v[2]];
        auto outward=normalize((b-a)%(c-a));
        require(outward*((a+b+c)/3.f)>0,"Publication winding points inward");
        for(int corner=0;corner<3;++corner)
          require(mesh.vertnorm[mesh.facengr[fi][corner]]*outward>0.999f,"Hard face normals were changed during publication");
      }
    }
    publishBrushes({csg::ramp({2,2,2})},"ramp publication");
    publishBrushes({csg::cylinder(1,2,16)},"cylinder publication");
    for(int mode=0;mode<3;++mode) {
      csg::Document generatedDoc; generatedDoc.assignIds(generatedDoc.root);
      csg::Node shape; shape.parametric=true; shape.extrusion.mode=csg::ExtrusionMode(mode);
      shape.extrusion.polygon={{0,0,0},{2,0,0},{2,2,0},{0,2,0}};
      shape.extrusion.path={{{0,0,0},{},{0,0,-1}},{{1,0,-4},{0,0,1},{}}};
      shape.extrusion.surfaces.resize(shape.extrusion.polygon.size()+2,{shape.extrusion.surface,true});
      shape.extrusion.surfaces[2].surface.offsetU=0.375;
      shape.extrusion.surfaces[2].surface.rotation=17;
      shape.extrusion.surfaces[2].automaticUv=false;
      generatedDoc.assignIds(shape); generatedDoc.root.children.push_back(shape);
      DataBlock savedShape; csg::saveDocument(generatedDoc,savedShape); csg::Document loadedShape; csg::Diagnostics shapeErrors;
      require(csg::loadDocument(savedShape,loadedShape,shapeErrors),"Parametric source did not reload");
      require(csg::fingerprint(loadedShape.root)==csg::fingerprint(generatedDoc.root),"Parametric source changed on reload");
      restore(std::move(loadedShape)); update(); require(current.success,"Parametric extrusion did not publish in Dagor");
      if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgMappingParity",false))
        for(const auto *node:published->nodes) for(float scale:{1.0f,0.75f})
          require(mappingEqual(mappingSnapshot(node->mesh->mesh,lightmapSize,lightmapSampleSize,false,scale),
                               mappingSnapshot(node->mesh->mesh,lightmapSize,lightmapSampleSize,true,scale)),
            "Parametric disk/memory UV parity failed");
    }
    DAEDITOR3.conNote("CSG parametric acceptance PASS: depth, spin, Bezier path, per-surface persistence, Dagor publication and UV packing parity");
    if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgMappingParity",false)) {
      csg::Document neighborhood; neighborhood.assignIds(neighborhood.root);
      for(unsigned i=0;i<33;++i) {
        csg::Node box; box.brush=csg::box({1,1,1}); box.transform.column[3]={i*0.02,0,0};
        neighborhood.assignIds(box); neighborhood.root.children.push_back(std::move(box));
      }
      for(double displacement:{0.0,0.03,0.12}) {
        neighborhood.root.children.back().transform.column[3].y=displacement;
        restore(neighborhood); update(); require(current.success,"Neighborhood UV parity geometry failed");
        for(const auto *node:published->nodes) for(int atlas:{32,128,1024}) for(float scale:{1.0f,0.75f})
          require(mappingEqual(mappingSnapshot(node->mesh->mesh,atlas,lightmapSampleSize,false,scale),
                               mappingSnapshot(node->mesh->mesh,atlas,lightmapSampleSize,true,scale)),
            "Neighborhood disk/memory UV parity failed");
      }
      DAEDITOR3.conNote("CSG neighborhood UV parity PASS: 32 neighbors, three edits, 32/128/1024 atlases and repeated 1/0.75 packing scales");
    }
    if(auto *library=EDITORCORE->queryEditorInterface<IEditorPrimitiveGeometry>()) {
      for(auto kind:{IEditorPrimitiveGeometry::Sphere}) {
        restore(source); selected=document.root.id;
        StaticGeometryContainer geometry; require(library->generate(kind,16,geometry),"Native primitive builder failed");
        for(auto *node:geometry.nodes) { node->wtm.setcol(0,Point3(2,0,0)); node->wtm.setcol(1,Point3(0,2,0)); node->wtm.setcol(2,Point3(0,0,2)); }
        try { addNativeGeometry(geometry,"Sphere"); } catch(const UiEditFinished &) {}
        require(editErrors.empty(),"Native primitive could not become a closed CSG source");
        update(); require(current.success,"Native primitive crossing room floor did not publish");
      }
      DAEDITOR3.conNote("CSG native primitives acceptance PASS: existing Dagor sphere builder, room-floor booleans and Jolt publication");
    }
    const char *meshFixture=dgs_get_settings()->getBlockByNameEx("debug")->getStr("csgAcceptanceMesh","");
    if(*meshFixture) {
      csg::Document empty; empty.assignIds(empty.root); restore(empty); selected=document.root.id;
      StaticGeometryContainer geometry; require(dagGeom->staticGeometryContainerLoadFromDag(geometry,meshFixture,nullptr),"DAG fixture did not load");
      try { addNativeGeometry(geometry,meshFixture,true); } catch(const UiEditFinished &) {}
      require(editErrors.empty() && !document.root.children.empty() && document.root.children.back().closedMesh,"DAG import did not retain closed mesh source");
      update(); require(current.success,"Imported DAG did not publish");
      DataBlock savedMesh; csg::saveDocument(document,savedMesh); csg::Document loadedMesh; csg::Diagnostics meshErrors;
      require(csg::loadDocument(savedMesh,loadedMesh,meshErrors) && csg::fingerprint(loadedMesh.root)==csg::fingerprint(document.root),"Imported mesh source did not persist");
      DAEDITOR3.conNote("CSG DAG import acceptance PASS: existing loader, closed mesh, UV/smoothing conversion, persistence and Jolt publication");
    }
    auto pulled=cube;
    require(csg::moveVertices(pulled,pulled.faces[0].vertices,{0,0,-0.5},modellingErrors),"Face push/pull rejected");
    publishBrushes({pulled},"push/pull publication");
    auto bevelled=cube; require(csg::bevel(bevelled,{0,1},0.1,100,modellingErrors),"Edge bevel rejected");
    publishBrushes({bevelled},"bevel publication");
    auto front=cube,back=cube;
    require(csg::clip(front,{1,0,0},0,100,{},modellingErrors) && csg::clip(back,{-1,0,0},0,101,{},modellingErrors),"Plane split failed");
    require(std::abs(csg::volume(front)+csg::volume(back)-8)<1e-8,"Split changed solid volume");
    publishBrushes({front,back},"split publication");
    csg::Mesh prism;
    require(csg::extrudeFace(cube,0,0.5,prism,modellingErrors),"Face extrusion failed");
    publishBrushes({cube,prism},"face extrusion publication");
    std::vector<csg::Mesh> outlinePrisms;
    require(csg::extrudeOutline({{0,0,0},{2,0,0},{2,0,1},{1,0,1},{1,0,2},{0,0,2}},{0,2,0},outlinePrisms,modellingErrors),"Concave outline extrusion failed");
    publishBrushes(std::move(outlinePrisms),"outline extrusion publication");
    std::vector<csg::Mesh> steps;
    for(int i=0;i<8;++i) { csg::Transform tm; tm.column[3]={0,0.1+i*0.2,i*0.4}; steps.push_back(csg::transformed(csg::box({2,0.2,0.4}),tm)); }
    publishBrushes(std::move(steps),"repeated stairs publication");
    auto surfaced=cube; surfaced.faces[0].surface.scaleU=0.25; surfaced.faces[0].surface.rotation=45;
    const char *testMaterial=dgs_get_settings()->getBlockByNameEx("debug")->getStr("csgAcceptanceMaterial","");
    surfaced.faces[0].surface.material=testMaterial;
    surfaced.faces[1].surface.worldLocked=true; surfaced.faces[1].surface.smoothing=1;
    csg::alignSurface(surfaced.faces[2].surface,surfaced.faces[0].surface);
    publishBrushes({surfaced},"surface and smoothing publication");
    if(*testMaterial)
    {
      bool found=false;
      for(const auto *node:published->nodes) for(const auto &material:node->mesh->mats)
        if(material && !strcmp(material->name.str(),testMaterial)) found=true;
      require(found,"Per-face Dagor material was lost during publication");
      DAEDITOR3.conNote("CSG per-face project material acceptance PASS: %s",testMaterial);
    }
    csg::Document precision; precision.assignIds(precision.root);
    csg::Node precisionOuter; precisionOuter.brush=csg::box({2,2,2}); precisionOuter.transform.column[3]={1000,0,1000};
    precision.assignIds(precisionOuter); precision.root.children.push_back(precisionOuter);
    csg::Node precisionCut; precisionCut.brush=csg::box({0.01,3,3}); precisionCut.transform.column[3]={1000,0,1000};
    precisionCut.operation=csg::Operation::Subtract; precision.assignIds(precisionCut); precision.root.children.push_back(precisionCut);
    restore(std::move(precision)); update(); require(current.success,"Centimeter cut at kilometer offset did not publish");
    std::vector<std::pair<float,float>> intervals;
    for(const auto *node:published->nodes)
    {
      float lo=1e30f,hi=-1e30f;
      for(auto p:node->mesh->mesh.vert) { p=node->wtm*p; lo=std::min(lo,p.x); hi=std::max(hi,p.x); }
      intervals.emplace_back(lo,hi);
    }
    std::sort(intervals.begin(),intervals.end()); require(intervals.size()==2,"Centimeter cut components merged during publication");
    float gap=intervals[1].first-intervals[0].second;
    require(gap>0.0099f && gap<0.0101f,"Dagor float conversion lost centimeter gap at kilometer offset");
    DAEDITOR3.conNote("CSG precision publication acceptance PASS: 1 cm cut at 1 km, actual Dagor gap %.9g m",gap);
    restore(source); update(); require(current.success,"Restore acceptance room after modelling failed");
    DAEDITOR3.conNote("CSG modelling publication acceptance PASS: box/ramp/cylinder, push/pull, bevel, split, face extrusion, concave outline, repeated stairs, UV alignment/locking/smoothing");
    DataBlock saved; csg::saveDocument(document,saved);
    csg::Document loaded; csg::Diagnostics errors;
    require(csg::loadDocument(saved,loaded,errors),"Document round trip failed");
    require(csg::fingerprint(loaded.root)==csg::fingerprint(document.root),"Document round trip changed source data");
    DataBlock future(saved); future.setInt("version",999); auto beforeLoad=loaded;
    require(!csg::loadDocument(future,loaded,errors),"Unsupported version was accepted");
    require(csg::fingerprint(loaded.root)==csg::fingerprint(beforeLoad.root),"Rejected load changed source data");
    require(!document.root.children.empty(),"Acceptance scene is empty");
    uint64_t before=csg::fingerprint(document.root);
    try { edit("CSG acceptance transform",[&] { document.root.children[0].transform.column[3].x+=0.25; return true; }); }
    catch(const UiEditFinished &) {}
    uint64_t changed=csg::fingerprint(document.root); require(changed!=before,"Edit did not change document");
    owner.getUndoSystem()->undo(); require(csg::fingerprint(document.root)==before,"Undo did not restore document");
    owner.getUndoSystem()->redo(); require(csg::fingerprint(document.root)==changed,"Redo did not restore edit");
    owner.getUndoSystem()->undo(); update(); require(current.success,"Valid document failed publication after undo");
    selected=document.root.children[0].id; mode=0; activateSelection();
    BBox3 selectionBox;
    require(gizmo->isSelected() && gizmo->getWorldBox(selectionBox),"Hierarchy selection did not activate native gizmo");
    require(selectionBox.width().x>7.9f,"Native focus bounds do not include the selected room");
    owner.onClick(CM_OBJED_MODE_MOVE,nullptr); owner.gizmoStarted();
    gizmo->moveObject(Point3(0.25f,0,0),IEditorCoreEngine::BASIS_World); owner.gizmoEnded(true);
    require(csg::fingerprint(document.root)!=before,"Native move gizmo did not change source");
    owner.getUndoSystem()->undo(); require(csg::fingerprint(document.root)==before,"Native move undo failed");
    for(bool scale:{false,true}) {
      selected=document.root.children[0].id; activateSelection();
      owner.onClick(scale ? CM_OBJED_MODE_SCALE:CM_OBJED_MODE_ROTATE,nullptr); owner.gizmoStarted();
      if(scale) gizmo->scaleObject(Point3(1.1f,1.1f,1.1f),gizmo->getPos(),IEditorCoreEngine::BASIS_World);
      else gizmo->rotateObject(Point3(0,0.2f,0),gizmo->getPos(),IEditorCoreEngine::BASIS_World);
      owner.gizmoEnded(true); update();
      require(current.success && csg::fingerprint(document.root)!=before,"Native rotation/scale did not publish");
      owner.getUndoSystem()->undo(); update();
      require(current.success && csg::fingerprint(document.root)==before,"Native rotation/scale undo failed");
    }
    selected=document.root.children[0].id; activateSelection(); owner.gizmoStarted();
    gizmo->moveObject(Point3(0.25f,0,0),IEditorCoreEngine::BASIS_World); owner.gizmoEnded(false);
    require(csg::fingerprint(document.root)==before,"Cancelled native gizmo left source changed");
    require(duplicateSelection(),"Native source duplication was not handled");
    require(csg::fingerprint(document.root)!=before,"Native duplicate did not change source");
    owner.getUndoSystem()->undo(); require(csg::fingerprint(document.root)==before,"Native duplicate undo failed");
    selected=document.root.children[0].id; activateSelection();
    owner.onClick(CM_OBJED_DELETE,nullptr);
    require(csg::fingerprint(document.root)!=before,"Native Delete did not remove selected source");
    owner.getUndoSystem()->undo(); require(csg::fingerprint(document.root)==before,"Native Delete undo failed");
    update(); require(current.success,"Native gizmo tests did not restore valid publication");
    DAEDITOR3.conNote("CSG native selection acceptance PASS: hierarchy activation, focus bounds, move/rotate/scale, cancel, duplicate, Delete and undo");
    auto *previous=published;
    document.root.children[0].brush.vertices[0].x=std::nan(""); dirty=true; update();
    require(!current.success && published==previous,"Failed evaluation replaced last valid publication");
    require(!validForExport(),"Invalid document was allowed to export");
    restore(source); update(); require(validForExport(),"Repaired document still blocks export");
    StaticGeometryContainer visual,collision; gather(visual,false); gather(collision,true);
    require(!visual.nodes.empty() && visual.nodes.size()==collision.nodes.size(),"Visual/collision gathering differs");
    for(int i=0;i<visual.nodes.size();++i)
      require(visual.nodes[i]->mesh->mesh.face.size()==collision.nodes[i]->mesh->mesh.face.size(),"Collision geometry differs from visual geometry");
    DAEDITOR3.conNote("CSG in-editor acceptance PASS: persistence, rejected load, native undo/redo, stale publication, export blocking, repaired publication, visual/collision gathering");
  }
  catch(const std::exception &error) { DAEDITOR3.conError("CSG in-editor acceptance FAIL: %s",error.what()); }
}
void BrushEditor::startBenchmark()
{
  benchmarkSource=std::make_unique<csg::Document>(document);
  document={}; document.root.name="Full pipeline benchmark"; document.assignIds(document.root);
  for(unsigned i=0;i<1000;++i)
  {
    csg::Node node; node.name="Benchmark box"; node.brush=csg::box({1,1,1});
    node.transform.column[3]={double(i%40)*4,0,double(i/40)*4};
    document.assignIds(node); document.root.children.push_back(std::move(node));
  }
  benchmarkNeighbors=std::clamp(dgs_get_settings()->getBlockByNameEx("debug")->getInt("csgBenchmarkNeighbors",0),0,32);
  benchmarkEdited=document.root.children[500].id;
  if(benchmarkNeighbors)
  {
    csg::Node group; group.id=document.allocate(); group.name="Overlapping neighborhood";
    for(int i=0;i<=benchmarkNeighbors;++i)
    {
      auto node=std::move(document.root.children[i]); node.transform.column[3]={i*0.02,0,0};
      group.children.push_back(std::move(node));
    }
    benchmarkEdited=group.children.back().id;
    document.root.children.erase(document.root.children.begin(),document.root.children.begin()+benchmarkNeighbors+1);
    document.root.children.insert(document.root.children.begin(),std::move(group));
  }
  benchmarkFrame=0; benchmarkWorst=0; dirty=true;
  DAEDITOR3.conNote("CSG benchmark protocol 1: brushes=1000 neighbors=%d max_input_faces=6 warmup=3 measured=10 atlas=%d sample=%.9g source=%llu edits=Y(frame*0.01m)",
    benchmarkNeighbors,lightmapSize,lightmapSampleSize,csg::fingerprint(document.root));
}
void BrushEditor::render() { for(auto &part:parts) dagGeom->geomObjectRender(*part.second.geometry); }
void BrushEditor::renderTrans() { for(auto &part:parts) dagGeom->geomObjectRenderTrans(*part.second.geometry); }
void BrushEditor::renderHandles()
{
  if (!isVisible()) return;
  const auto *node=document.find(selected); if (!node) return;
  std::function<void(const csg::Node &,csg::Transform)> visit=[&](const csg::Node &n,csg::Transform tm) {
    tm=compose(tm,n.transform);
    if (n.id==selected)
    {
      csg::Mesh generated; csg::Diagnostics errors; const auto *source=&n.brush;
      if(n.parametric && csg::generateExtrusion(n.extrusion,generated,errors)) source=&generated;
      auto mesh=csg::transformed(*source,tm);
      dagRender->setLinesTm(TMatrix::IDENT);
      E3DCOLOR color=current.success ? E3DCOLOR(255,230,80):E3DCOLOR(255,60,30);
      for (size_t fi=0;fi<mesh.faces.size();++fi)
      {
        const auto &f=mesh.faces[fi];
        for (size_t i=0;i<f.vertices.size();++i)
          dagRender->renderLine(point(mesh.vertices[f.vertices[i]]),point(mesh.vertices[f.vertices[(i+1)%f.vertices.size()]]),
            mode==1 && int(fi)==faceIndex ? E3DCOLOR(255,255,255):color);
      }
      for (auto i:components) if (i<mesh.vertices.size())
      {
        auto p=mesh.vertices[i]; constexpr double r=0.04;
        dagRender->renderLine(point(p-csg::Vec{r,0,0}),point(p+csg::Vec{r,0,0}),E3DCOLOR(255,255,255));
        dagRender->renderLine(point(p-csg::Vec{0,r,0}),point(p+csg::Vec{0,r,0}),E3DCOLOR(255,255,255));
      }
    }
    for (const auto &c:n.children) visit(c,tm);
  }; visit(document.root,{});
}
bool BrushEditor::pick(IGenViewportWnd *vp,int x,int y,bool toggle)
{
  if (!isVisible()) return false;
  Point3 o,d; vp->clientToWorld(Point2(x,y),o,d); double closest=1e30;
  csg::Id id=0; int hitFace=0; csg::Mesh hitMesh;
  std::function<void(const csg::Node &,csg::Transform)> visit=[&](const csg::Node &n,csg::Transform tm) {
    if (!n.visible) return; tm=compose(tm,n.transform);
    csg::Mesh generated; csg::Diagnostics errors; const auto *source=&n.brush;
    if(n.parametric && csg::generateExtrusion(n.extrusion,generated,errors)) source=&generated;
    auto mesh=csg::transformed(*source,tm);
    for (size_t fi=0;fi<mesh.faces.size();++fi)
    {
      const auto &f=mesh.faces[fi];
      for (size_t i=1;i+1<f.vertices.size();++i)
        if (rayTriangle(vec(o),vec(d),mesh.vertices[f.vertices[0]],mesh.vertices[f.vertices[i]],mesh.vertices[f.vertices[i+1]],closest))
        { id=n.id; hitFace=int(fi); hitMesh=mesh; }
    }
    for (const auto &c:n.children) visit(c,tm);
  }; visit(document.root,{});
  if (!id) return false;
  if(const auto *node=document.find(id); node && (node->parametric || node->closedMesh)) mode=0;
  if (!toggle || selected!=id) components.clear(); selected=id; faceIndex=hitFace;
  if (mode==1) components=hitMesh.faces[hitFace].vertices;
  if (mode==2 || mode==3)
  {
    auto &face=hitMesh.faces[hitFace]; double best=1e30; std::vector<uint32_t> indices;
    for (size_t i=0;i<face.vertices.size();++i)
    {
      auto a=face.vertices[i],b=face.vertices[(i+1)%face.vertices.size()]; Point2 pa,pb; real z;
      if (!vp->worldToClient(point(hitMesh.vertices[a]),pa,&z) || z<=0) continue;
      double t=0;
      if (mode==2 && vp->worldToClient(point(hitMesh.vertices[b]),pb,&z) && z>0)
      {
        double dx=pb.x-pa.x,dy=pb.y-pa.y,l=dx*dx+dy*dy;
        if (l>0) t=std::clamp(((x-pa.x)*dx+(y-pa.y)*dy)/l,0.0,1.0);
        pa=pa+(pb-pa)*float(t);
      }
      double dist=(pa.x-x)*(pa.x-x)+(pa.y-y)*(pa.y-y);
      if (dist<best) { best=dist; indices=mode==2 ? std::vector<uint32_t>{a,b}:std::vector<uint32_t>{a}; }
    }
    for (auto i:indices)
    {
      auto found=std::find(components.begin(),components.end(),i);
      if (found==components.end()) components.push_back(i); else if (toggle) components.erase(found);
    }
  }
  activateSelection();
  DAGORED2->invalidateViewportCache(); return true;
}
bool BrushEditor::validForExport() { update(); return !loadFailed && current.success; }
void BrushEditor::gather(StaticGeometryContainer &container,bool collision)
{
  if (!validForExport() || !published) return;
  for (const auto *source:published->nodes)
  {
    auto *node=dagGeom->newStaticGeometryNode(*source);
    if (collision) node->flags&=~StaticGeometryNode::FLG_RENDERABLE;
    container.addNode(node);
  }
}

void BrushEditor::syncGizmo()
{
  if (!gizmo) return;
  if (!isVisible()) { gizmo->setFlags(0,RenderableEditableObject::FLG_SELECTED,false); return; }
  csg::Transform world;
  std::function<bool(const csg::Node &,csg::Transform)> find=[&](const csg::Node &n,csg::Transform parent) {
    auto tm=compose(parent,n.transform); if (n.id==selected) { world=tm; return true; }
    for (const auto &c:n.children) if (find(c,tm)) return true; return false;
  };
  if (!find(document.root,{})) return;
  const auto *node=document.find(selected);
  if (mode && node && !node->closedMesh && !node->brush.faces.empty())
  {
    auto indices=components;
    if (mode==1) indices=node->brush.faces[std::clamp(faceIndex,0,int(node->brush.faces.size())-1)].vertices;
    csg::Vec center{}; size_t count=0;
    for (auto i:indices) if (i<node->brush.vertices.size()) { center=center+world.point(node->brush.vertices[i]); ++count; }
    if (count) world.column[3]=center/double(count);
  }
  TMatrix tm; for (int i=0;i<4;++i) tm.setcol(i,point(world.column[i])); gizmo->setWtm(tm);
}
void BrushEditor::putTransformUndo()
{ owner.getUndoSystem()->put(new BrushUndo(*this,document,document)); }
void BrushEditor::activateSelection()
{
  for(int i=0;i<owner.objectCount();++i) owner.getObject(i)->setFlags(0,RenderableEditableObject::FLG_SELECTED,false);
  gizmo->setFlags(RenderableEditableObject::FLG_SELECTED,RenderableEditableObject::FLG_SELECTED,false);
  syncGizmo(); owner.updateSelection(); owner.updateGizmo();
}
bool BrushEditor::selectionBounds(BBox3 &box) const
{
  box.setempty(); bool found=false;
  std::function<void(const csg::Node &,csg::Transform,bool)> visit=[&](const csg::Node &n,csg::Transform parent,bool branch) {
    auto tm=compose(parent,n.transform); branch=branch || n.id==selected;
    if(branch) {
      csg::Mesh generated; csg::Diagnostics errors; const auto *source=&n.brush;
      if(n.parametric && csg::generateExtrusion(n.extrusion,generated,errors)) source=&generated;
      for(auto p:source->vertices) { box+=point(tm.point(p)); found=true; }
    }
    for(const auto &child:n.children) visit(child,tm,branch);
  }; visit(document.root,{},false); return found;
}
bool BrushEditor::deleteSelection()
{
  if(!gizmo->isSelected() || selected==document.root.id) return false;
  try { edit("Delete CSG node",[&] {
    auto *parent=parentOf(document.root,selected); if(!parent) return false;
    auto id=selected;
    parent->children.erase(std::remove_if(parent->children.begin(),parent->children.end(),[&](const csg::Node &n){return n.id==id;}),parent->children.end());
    selected=parent->id; components.clear(); return true;
  }); } catch(const UiEditFinished &) {}
  return true;
}
bool BrushEditor::duplicateSelection()
{
  if(!gizmo->isSelected() || selected==document.root.id) return false;
  try { edit("Duplicate CSG node",[&] {
    auto *node=document.find(selected),*parent=parentOf(document.root,selected); if(!node || !parent) return false;
    auto copy=*node; document.assignIds(copy); copy.name+=" copy"; selected=copy.id;
    parent->children.push_back(std::move(copy)); components.clear(); return true;
  }); } catch(const UiEditFinished &) {}
  return true;
}
void BrushEditor::transformSelection(const TMatrix &before,const TMatrix &after)
{
  auto *node=document.find(selected); if (!node) return;
  csg::Transform oldTm,newTm,parent;
  for (unsigned i=0;i<4;++i) { oldTm.column[i]=vec(before.getcol(i)); newTm.column[i]=vec(after.getcol(i)); }
  std::function<bool(const csg::Node &,csg::Transform)> find=[&](const csg::Node &n,csg::Transform tm) {
    if (n.id==selected) { parent=tm; return true; }
    tm=compose(tm,n.transform); for (const auto &c:n.children) if (find(c,tm)) return true; return false;
  }; find(document.root,{});
  auto world=compose(parent,node->transform);
  if (std::abs(oldTm.determinant())<1e-12 || std::abs(newTm.determinant())<1e-12) { syncGizmo(); return; }
  auto map=[&](csg::Vec p) { return newTm.point(oldTm.inversePoint(p)); };
  editErrors.clear();
  if (mode && !node->closedMesh && !node->brush.faces.empty())
  {
    auto indices=mode==1 ? node->brush.faces[std::clamp(faceIndex,0,int(node->brush.faces.size())-1)].vertices:components;
    auto candidate=node->brush; std::set<uint32_t> unique(indices.begin(),indices.end());
    for (auto i:unique) if (i<candidate.vertices.size()) candidate.vertices[i]=world.inversePoint(map(world.point(candidate.vertices[i])));
    if (!csg::validate(candidate,editErrors,node->id,true)) { syncGizmo(); return; }
    node->brush=std::move(candidate);
  }
  else
  {
    csg::Transform tm; auto origin=parent.inversePoint(map(world.column[3])); tm.column[3]=origin;
    for (unsigned i=0;i<3;++i) tm.column[i]=parent.inversePoint(map(world.column[3]+world.column[i]))-origin;
    node->transform=tm;
  }
  dirty=true; DAGORED2->invalidateViewportCache();
}
