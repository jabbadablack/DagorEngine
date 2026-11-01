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
#include <ioSys/dag_dataBlock.h>
#include <oldEditor/de_workspace.h>
#include <startup/dag_globalSettings.h>
#include <imgui/imgui.h>
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
public:
  BrushUndo(BrushEditor &e,csg::Document b,csg::Document a):editor(e),before(std::move(b)),after(std::move(a)) {}
  void restore(bool saveRedo) override { if (saveRedo) after=editor.document; editor.restore(before); }
  void redo() override { editor.restore(after); }
  size_t size() override
  {
    std::function<size_t(const csg::Node &)> storage=[&](const csg::Node &node) {
      size_t bytes=node.name.capacity()+1+node.cutSurface.material.capacity()+1;
      bytes+=node.children.capacity()*sizeof(csg::Node)+node.brush.vertices.capacity()*sizeof(csg::Vec)+
        node.brush.faces.capacity()*sizeof(csg::Face);
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
  auto before=document; editErrors.clear();
  if (!action()) { document=std::move(before); throw UiEditFinished{}; }
  owner.getUndoSystem()->begin(); owner.getUndoSystem()->put(new BrushUndo(*this,std::move(before),document));
  owner.getUndoSystem()->accept(label); dirty=true; activateSelection();
  DAGORED2->invalidateViewportCache();
  throw UiEditFinished{}; // Unwind references into vectors changed by this edit.
}
void BrushEditor::add(csg::Mesh mesh,const char *name)
{
  if (!csg::validate(mesh,editErrors,0,true)) return;
  edit("Create CSG brush",[&] {
    auto *parent=document.find(selected); if (!parent || !parent->brush.faces.empty()) parent=&document.root;
    csg::Node n; n.name=name; n.brush=std::move(mesh); document.assignIds(n); selected=n.id;
    parent->children.push_back(std::move(n)); components.clear(); return true;
  });
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
  if (n.brush.faces.empty() && ImGui::BeginDragDropTarget())
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
void BrushEditor::surfaces(csg::Node &n)
{
  if (n.brush.faces.empty())
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
  faceIndex=std::clamp(faceIndex,0,int(n.brush.faces.size())-1);
  auto &s=n.brush.faces[faceIndex].surface; csg::Surface proposed=s;
  char material[512]; std::snprintf(material,sizeof(material),"%s",s.material.c_str());
  bool changed=ImGui::InputText("Material asset",material,sizeof(material),ImGuiInputTextFlags_EnterReturnsTrue);
  if(changed) proposed.material=material;
  ImGui::TextDisabled("Press Enter to apply the material asset.");
  changed|=inputDouble("U scale",proposed.scaleU); changed|=inputDouble("V scale",proposed.scaleV);
  changed|=inputDouble("U offset",proposed.offsetU); changed|=inputDouble("V offset",proposed.offsetV);
  changed|=inputDouble("UV rotation",proposed.rotation); changed|=ImGui::Checkbox("World locked",&proposed.worldLocked);
  int smoothing=int(proposed.smoothing); changed|=ImGui::InputInt("Smoothing mask (0 = hard)",&smoothing); proposed.smoothing=uint32_t(smoothing);
  if (changed) edit("Edit CSG surface",[&] { s=proposed; return csg::validate(n.brush,editErrors,n.id,true); });
  if (ImGui::Button("Copy mapping")) { copiedSurface=s; haveCopiedSurface=true; }
  ImGui::SameLine(); if (ImGui::Button("Align to copied mapping") && haveCopiedSurface)
    edit("Align CSG mapping",[&] { csg::alignSurface(s,copiedSurface); return true; });
  if (ImGui::Button("Apply surface to brush")) edit("Apply CSG surface",[&] { for (auto &f:n.brush.faces) f.surface=s; return true; });
  ImGui::InputText("Replace material",replaceFrom,sizeof(replaceFrom)); ImGui::InputText("With material",replaceTo,sizeof(replaceTo));
  if (ImGui::Button("Replace throughout model")) edit("Replace CSG material",[&] {
    std::function<void(csg::Node &)> replace=[&](csg::Node &node) {
      for (auto &f:node.brush.faces) if (f.surface.material==replaceFrom) f.surface.material=replaceTo;
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
    String state(96,"Test source %llu valid %d",csg::fingerprint(document.root),int(current.success));
    ImGui::Button(state.c_str());
  }
  if(benchmarkFrame>=0) { ImGui::Text("Full-pipeline benchmark frame %d / 13",benchmarkFrame); return; }
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgBenchmark",false) &&
    ImGui::Button("Run CSG release benchmark")) { startBenchmark(); return; }
  ImGui::TextWrapped("Create convex brushes, combine them in the hierarchy, then edit components and surfaces.");
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
    ImGui::InputFloat3("Dimensions",size); ImGui::InputInt("Cylinder sides",&cylinderSides);
    if (ImGui::Button("Box")) add(csg::box({size[0],size[1],size[2]}),"Box");
    ImGui::SameLine(); if (ImGui::Button("Ramp")) add(csg::ramp({size[0],size[1],size[2]}),"Ramp");
    ImGui::SameLine(); if (ImGui::Button("Cylinder")) add(csg::cylinder(size[0]*0.5,size[1],cylinderSides),"Cylinder");
    if (ImGui::Button("Operation group")) edit("Create CSG group",[&] {
      auto *parent=document.find(selected); if (!parent || !parent->brush.faces.empty()) parent=&document.root;
      csg::Node group; group.name="Group"; document.assignIds(group); selected=group.id; parent->children.push_back(std::move(group)); return true;
    });
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
  if (ImGui::InputText("Name",name,sizeof(name))) edit("Rename CSG node",[&]{n->name=name;return true;});
  bool enabled=n->visible;
  if (ImGui::Checkbox("Enabled",&enabled)) edit("Enable CSG node",[&]{n->visible=enabled;return true;});
  int op=int(n->operation);
  if (ImGui::Combo("Operation",&op,"Union\0Subtract\0Intersect\0")) edit("Set CSG operation",[&]{n->operation=csg::Operation(op);return true;});
  inputDouble("Grid spacing",grid); inputDouble("Angle snap (degrees)",angleSnap);
  csg::Transform transform=n->transform; bool changed=inputVec("Position",transform.column[3]);
  changed|=inputVec("X axis",transform.column[0]); changed|=inputVec("Y axis",transform.column[1]); changed|=inputVec("Z axis",transform.column[2]);
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
  if (ImGui::CollapsingHeader("Component modelling",ImGuiTreeNodeFlags_DefaultOpen)) { modelling(*n); if (dirty) return; }
  if (ImGui::CollapsingHeader("Surface mapping")) surfaces(*n);
  if (ImGui::CollapsingHeader("Lightmap UV preparation"))
  {
    int lm=lightmapSize; float sample=lightmapSampleSize;
    if (ImGui::InputInt("Atlas size",&lm) && lm>=16 && lm<=8192 && (lm&(lm-1))==0) { lightmapSize=lm;dirty=true; }
    if (ImGui::InputFloat("Sample size",&sample) && sample>0) { lightmapSampleSize=sample;dirty=true; }
    ImGui::TextWrapped("Uses Dagor auto-unwrapping and its existing chart padding. No lighting bake is performed.");
  }
}

bool BrushEditor::buildPublished(const csg::Mesh &polygons,StaticGeometryContainer &container)
{
  csg::Mesh source;
  if(!csg::triangulateForPublication(polygons,source,current.diagnostics))
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Triangulation did not produce a valid publication mesh"}); return false; }
  if (source.faces.empty()) return true;
  csg::Vec origin=source.vertices.front();
  auto *mesh=new Mesh;
  mesh->vert.resize(source.vertices.size());
  for (size_t i=0;i<source.vertices.size();++i) mesh->vert[i]=point(source.vertices[i]-origin);
  // Verify the actual float publication does not collapse valid geometry.
  csg::Mesh converted=source;
  for (size_t i=0;i<source.vertices.size();++i) converted.vertices[i]=vec(mesh->vert[i]);
  if (!csg::validate(converted,current.diagnostics))
  { current.diagnostics.push_back({csg::Code::InvalidResult,0,0,"Float publication collapsed geometry"}); delete mesh; return false; }
  MaterialDataList materials;
  std::map<std::string,int> materialIds;
  IAssetService *assets=EDITORCORE->queryEditorInterface<IAssetService>();
  for (const auto &face:source.faces)
  {
    int mat=0; auto found=materialIds.find(face.surface.material);
    if (found==materialIds.end())
    {
      MaterialData *data=nullptr;
      if (!face.surface.material.empty() && assets) data=assets->getMaterialData(face.surface.material.c_str());
      if (!face.surface.material.empty() && !data)
      {
        current.diagnostics.push_back({csg::Code::InvalidResult,face.sourceBrush,face.id,"Cannot resolve material asset: "+face.surface.material});
        delete mesh; return false;
      }
      if (!data)
      {
        DataBlock application(DAGORED2->getWorkspace().getAppBlkPath());
        bool dng=application.getBlockByNameEx("game")->getBool("daNetGameEditorRender",false);
        data=new MaterialData; data->className=dng ? "csg_static":"simple";
        data->mat.diff=Color4(0.7f,0.7f,0.7f,1);
        data->mat.power=0;
        if(dng && (defaultTexture.empty() || defaultNormalTexture.empty()))
        {
          current.diagnostics.push_back({csg::Code::InvalidResult,face.sourceBrush,face.id,
            "Set brushEditorSettings/defaultTexture and defaultNormalTexture to project texture assets, or assign a static material asset"});
          delete data; delete mesh; return false;
        }
        data->mtex[0]=dagRender->addManagedTexture(defaultTexture.empty() ?
          editorcore_extapi::make_full_start_path("../commonData/tex/missing.dds"):defaultTexture.c_str());
        if(dng) data->mtex[2]=dagRender->addManagedTexture(defaultNormalTexture.c_str());
      }
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
        auto uv=csg::textureCoordinates(face.surface,source.vertices[triangle.v[j]]);
        tex.t[j]=mesh->tvert[0].size(); mesh->tvert[0].push_back(Point2(float(uv[0]),float(uv[1])));
      }
      mesh->tface[0].push_back(tex);
    }
  }
  if (lightmapSize<16 || lightmapSize>8192 || (lightmapSize&(lightmapSize-1)) ||
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
  const auto &mesh=*current.mesh;
  std::vector<uint32_t> parent(mesh.vertices.size());
  for(uint32_t i=0;i<parent.size();++i) parent[i]=i;
  auto root=[&](uint32_t i) { while(parent[i]!=i) { parent[i]=parent[parent[i]]; i=parent[i]; } return i; };
  for(const auto &face:mesh.faces) for(auto i:face.vertices) parent[root(i)]=root(face.vertices[0]);
  std::map<uint32_t,csg::Mesh> components;
  std::map<uint32_t,std::map<uint32_t,uint32_t>> remaps;
  for(const auto &face:mesh.faces)
  {
    auto component=root(face.vertices[0]); auto &out=components[component]; auto &remap=remaps[component]; auto f=face;
    for(auto &index:f.vertices)
    {
      auto inserted=remap.emplace(index,uint32_t(remap.size()));
      if(inserted.second) out.vertices.push_back(mesh.vertices[index]);
      index=inserted.first->second;
    }
    out.faces.push_back(std::move(f));
  }
  // A cavity's inward boundary is not a standalone positive solid. Keep the
  // complete result together when shell topology requires that relationship.
  for(const auto &component:components) if(csg::volume(component.second)<=0)
  { components.clear(); components.emplace(0,mesh); break; }
  std::map<uint64_t,PublishedPart> nextParts;
  auto partitionedAt=std::chrono::steady_clock::now();
  double mappingMs=0,renderCollisionMs=0,joltMs=0;
  auto container=std::make_unique<StaticGeometryContainer>();
  auto discardNew=[&] {
    for(auto &part:nextParts) if(!parts.count(part.first) && part.second.geometry) dagGeom->deleteGeomObject(part.second.geometry);
  };
  for(auto &component:components)
  {
    csg::Node key; key.brush=std::move(component.second);
    key.transform.column[3]={double(lightmapSize),lightmapSampleSize,0};
    uint64_t hash=csg::fingerprint(key);
    PublishedPart part;
    auto previous=parts.find(hash);
    if(previous!=parts.end()) part=previous->second;
    else
    {
      part.container=std::make_shared<StaticGeometryContainer>();
      auto mapStart=std::chrono::steady_clock::now();
      if(!buildPublished(key.brush,*part.container)) { discardNew(); current.success=false; return; }
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
    DAEDITOR3.conNote("CSG native selection acceptance PASS: hierarchy activation, focus bounds, move, cancel, duplicate, Delete and undo");
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
      auto mesh=csg::transformed(n.brush,tm);
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
    auto mesh=csg::transformed(n.brush,tm);
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
  if (mode && node && !node->brush.faces.empty())
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
    if(branch) for(auto p:n.brush.vertices) { box+=point(tm.point(p)); found=true; }
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
  if (mode && !node->brush.faces.empty())
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
