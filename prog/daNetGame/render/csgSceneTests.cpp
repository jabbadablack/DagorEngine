// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <csg/ecs.h>
#include <daECS/core/entityManager.h>
#include <daECS/core/componentTypes.h>
#include <gamePhys/collision/collisionLib.h>
#include <gamePhys/collision/collisionCache.h>
#include <debug/dag_debug.h>
#include <debug/dag_logSys.h>
#include <cmath>
#include <chrono>
#include <render/lruCollision.h>
#include <algorithm>
#include <util/dag_delayedAction.h>
#include <osApiWrappers/dag_miscApi.h>
#include <startup/dag_globalSettings.h>
#include <util/dag_console.h>
#include "camera/sceneCam.h"
#include "render/screencap.h"
#include "render/renderer.h"
#include <drv/3d/dag_lock.h>
#include <drv/3d/dag_info.h>

bool run_csg_runtime_acceptance(ecs::EntityId root)
{
  const auto *loaded=csg::getSceneDocument(root);
  if(!loaded || loaded->root.name!="Acceptance room and stairs") {
    logerr("CSG runtime authoring acceptance FAIL: expected the isolated acceptance fixture"); return false;
  }
  auto original=*loaded;
  struct Restore
  {
    ecs::EntityId root; csg::Document source;
    ~Restore() { csg::Diagnostics errors; if(!csg::updateScene(root,std::move(source),errors)) logerr("CSG runtime fixture restore FAILED"); }
  } restore{root,original};
  auto require=[](bool value,const char *message) {
    if(!value) logerr("CSG runtime authoring acceptance FAIL: %s",message); return value;
  };
  auto ray=[] { float distance=6; return dacoll::traceray_normalized_frt({2,1.5,0},{0,0,-1},distance,nullptr,nullptr); };
  auto sphere=[] { dacoll::ShapeQueryOutput hit; return dacoll::sphere_cast({2,1.5,0},{2,1.5,-6},0.1f,hit); };
  auto giHandles=[] {
    std::vector<rendinst::riex_handle_t> handles;
    LRURendinstCollision::gatherWorldCollisions(BBox3(Point3(-100,-100,-100),Point3(100,100,100)),
      [&](auto handle) { handles.push_back(handle); });
    std::sort(handles.begin(),handles.end()); return handles;
  };
  auto initialGi=giHandles();
  auto giCache=LRURendinstCollision::acquire();
  if(!require(!initialGi.empty() && giCache->updateLRU({initialGi.data(),initialGi.size()}),
      "runtime geometry enters the existing GI collision GPU cache")) return false;
  for(auto handle:initialGi)
    if(!require(bool(giCache->getModelData(LRURendinstCollision::worldCollisionType(handle))),
        "GI collision has published GPU geometry")) return false;
  if(!require(ray() && sphere(),"uncut wall must block ray and Jolt sweep")) return false;
  TraceMeshFaces cache; bbox3f box;
  BBox3 bounds(Point3(1.9f,1.4f,-4.5f),Point3(2.1f,1.6f,0.1f)); box=v_ldu_bbox3(bounds);
  dacoll::validate_trace_cache(box,v_zero(),0,&cache);
  if(!require(dacoll::try_use_trace_cache(box,&cache),"initial trace cache is usable")) return false;
  auto stableId=original.root.children.front().id;
  auto stableEntity=csg::getSourceEntity(root,stableId);
  auto candidate=original; csg::Node cutter; cutter.name="Runtime acceptance window";
  cutter.operation=csg::Operation::Subtract; cutter.brush=csg::box({1,1,2}); cutter.transform.column[3]={2,1.5,-4};
  candidate.assignIds(cutter); auto cutterId=cutter.id; candidate.root.children.push_back(std::move(cutter));
  csg::Diagnostics errors;
  if(!require(csg::updateScene(root,std::move(candidate),errors),"cut publication")) return false;
  if(!require(!ray() && !sphere(),"successful cut must clear ray and Jolt sweep together")) return false;
  auto acceptedGi=giHandles();
  if(!require(acceptedGi!=initialGi,"cut publishes a changed GI collision revision")) return false;
  for(auto handle:initialGi) if(!std::binary_search(acceptedGi.begin(),acceptedGi.end(),handle))
    if(!require(LRURendinstCollision::worldCollisionType(handle)==~0u,"retired GI handle cannot resolve stale geometry")) return false;
  if(!require(!dacoll::try_use_trace_cache(box,&cache),"cut invalidates old static trace cache")) return false;
  dacoll::validate_trace_cache(box,v_zero(),0,&cache);
  if(!require(dacoll::try_use_trace_cache(box,&cache),"new static trace cache is usable")) return false;
  auto cutterEntity=csg::getSourceEntity(root,cutterId);
  if(!require(cutterEntity!=ecs::INVALID_ENTITY_ID &&
      g_entity_mgr->getOr(cutterEntity,ECS_HASH("csg__operation"),-1)==int(csg::Operation::Subtract) &&
      g_entity_mgr->getOr(cutterEntity,ECS_HASH("csg__published"),false),"cutter has a published source entity")) return false;
  if(!require(csg::getSourceEntity(root,stableId)==stableEntity,"unaffected source keeps its ECS identity")) return false;
  auto acceptedMesh=csg::getSceneResult(root)->mesh; auto acceptedRevision=csg::getSceneResult(root)->revision;
  candidate=*csg::getSceneDocument(root); candidate.root.children.back().transform.column[0]={};
  errors.clear();
  if(!require(!csg::updateScene(root,std::move(candidate),errors) && !errors.empty(),"invalid runtime edit must fail")) return false;
  if(!require(csg::getSceneResult(root)->mesh==acceptedMesh && csg::getSceneResult(root)->revision==acceptedRevision &&
      csg::getSourceEntity(root,cutterId)==cutterEntity && !ray() && !sphere() && giHandles()==acceptedGi,
      "failure retains source, render, GI and collision revision")) return false;
  candidate=*csg::getSceneDocument(root);
  auto &badFace=candidate.root.children.front().brush.faces.front();
  auto badNode=badFace.sourceBrush,badSurface=badFace.id;
  badFace.surface.material="__csg_unexported_material__"; errors.clear();
  if(!require(!csg::updateScene(root,std::move(candidate),errors) &&
      std::any_of(errors.begin(),errors.end(),[&](const auto &e){return e.node==badNode && e.face==badSurface;}),
      "publication failure identifies the source brush and surface")) return false;
  if(!require(csg::getSceneResult(root)->mesh==acceptedMesh && csg::getSceneResult(root)->revision==acceptedRevision &&
      giHandles()==acceptedGi && !ray() && !sphere(),"publication failure retains the complete previous revision")) return false;
  errors.clear();
  if(!require(csg::updateScene(root,original,errors) && ray() && sphere(),"removing a cutter restores the wall")) return false;
  if(!require(csg::getSourceEntity(root,cutterId)==ecs::INVALID_ENTITY_ID &&
      csg::getSourceEntity(root,stableId)==stableEntity,"removed cutter disappears while existing sources stay stable")) return false;
  candidate=original;
  for(int mode=0;mode<3;++mode) {
    csg::Node shape; shape.name="Runtime parametric fixture"; shape.parametric=true;
    shape.transform.column[3]={30.0+mode*5,0,0}; auto &s=shape.extrusion;
    s.mode=csg::ExtrusionMode(mode); s.polygon={{1,-0.2,0},{1.4,-0.2,0},{1.4,0.2,0},{1,0.2,0}}; s.spinSides=16;
    if(s.mode==csg::ExtrusionMode::Path) s.polygon={{-0.1,-0.1,0},{0.1,-0.1,0},{0.1,0.1,0},{-0.1,0.1,0}};
    s.path={{{0,0,0},{},{0,0,-1}},{{2,1,-4},{-1,0,0},{}}};
    candidate.assignIds(shape); candidate.root.children.push_back(std::move(shape));
  }
  errors.clear(); bool parametric=csg::updateScene(root,std::move(candidate),errors);
  if(!parametric) for(const auto &error:errors) logerr("CSG runtime parametric fixture node %llu face %llu: %s",error.node,error.face,error.message.c_str());
  if(!require(parametric,"depth, spin and Bezier path runtime publication")) return false;
  candidate=original; candidate.root.children.clear(); errors.clear();
  if(!require(csg::updateScene(root,std::move(candidate),errors) && csg::getSceneResult(root)->mesh->faces.empty() &&
      !ray() && !sphere() && giHandles().empty(),"empty revision removes visual, GI and world collision outputs")) return false;
  debug("CSG runtime authoring acceptance PASS: live cut, source identities/cutter entities, invalid edit rollback, cache invalidation, Jolt sweeps, depth/spin/path, GI GPU geometry/retirement and empty publication");
  flush_debug_file();
  return true;
}

void run_csg_runtime_frame_acceptance(ecs::EntityId root)
{
  struct State {
    ecs::EntityId root;
    csg::Document original;
    csg::Id cutter=0;
    int step=0;
    bool restored=false;
    ~State() {
      if(!restored && csg::getSceneDocument(root)) {
        csg::Diagnostics errors;
        if(!csg::updateScene(root,std::move(original),errors)) logerr("CSG runtime frame fixture restore FAILED");
      }
    }
  };
  struct Step final : DelayedAction {
    std::shared_ptr<State> state;
    unsigned due;
    Step(std::shared_ptr<State> value,unsigned frame):state(std::move(value)),due(frame) {}
    bool precondition() override { return !csg::getSceneDocument(state->root) || dagor_frame_no()>=due; }
    void performAction() override {
      auto &s=*state; if(!csg::getSceneDocument(s.root)) return;
      if(csg::getSceneRenderedRevision(s.root)<csg::getSceneResult(s.root)->revision) {
        logerr("CSG runtime frame publication acceptance FAIL: preceding revision was not rendered"); return;
      }
      if(s.step==3) {
        debug("CSG runtime frame publication acceptance PASS: live cut, moved cut and restoration rendered on separate frames");
        flush_debug_file(); return;
      }
      auto candidate=*csg::getSceneDocument(s.root);
      if(s.step==0) {
        csg::Node cut; cut.name="Frame publication cutter"; cut.brush=csg::box({1,1,2});
        cut.operation=csg::Operation::Subtract; cut.transform.column[3]={2,1.5,-4};
        candidate.assignIds(cut); s.cutter=cut.id; candidate.root.children.push_back(std::move(cut));
      } else if(s.step==1) candidate.find(s.cutter)->transform.column[3].x=-2;
      else candidate=s.original;
      csg::Diagnostics errors;
      if(!csg::updateScene(s.root,std::move(candidate),errors)) {
        logerr("CSG runtime frame publication acceptance FAIL: update %d",s.step); return;
      }
      float distance=6; bool blocked=dacoll::traceray_normalized_frt({2,1.5,0},{0,0,-1},distance,nullptr,nullptr);
      dacoll::ShapeQueryOutput hit; bool swept=dacoll::sphere_cast({2,1.5,0},{2,1.5,-6},0.1f,hit);
      if(blocked!=(s.step!=0) || swept!=blocked) {
        logerr("CSG runtime frame publication acceptance FAIL: collision does not match update %d",s.step); return;
      }
      if(s.step==2) s.restored=true;
      ++s.step; add_delayed_action_buffered(new Step(state,dagor_frame_no()+1));
    }
  };
  auto state=std::make_shared<State>(); state->root=root; state->original=*csg::getSceneDocument(root);
  add_delayed_action_buffered(new Step(std::move(state),dagor_frame_no()+60));
}

bool run_csg_runtime_benchmark(ecs::EntityId root)
{
  const auto *loaded=csg::getSceneDocument(root); if(!loaded) return false;
  auto original=*loaded;
  // Same frozen protocol as the editor benchmark: six-face boxes, 33 ordered
  // overlapping neighbors and 967 disjoint brushes, standard 1024/0.1 UVs.
  csg::Document corpus; corpus.root.id=original.root.id; corpus.nextId=original.root.id+1;
  corpus.root.name="Full pipeline benchmark"; corpus.runtimeEditable=true;
  for(unsigned i=0;i<1000;++i) {
    csg::Node node; node.name="Benchmark box"; node.brush=csg::box({1,1,1});
    node.transform.column[3]={double(i%40)*4,0,double(i/40)*4};
    corpus.assignIds(node); corpus.root.children.push_back(std::move(node));
  }
  csg::Node group; group.id=corpus.allocate(); group.name="Overlapping neighborhood";
  for(unsigned i=0;i<33;++i) {
    auto node=std::move(corpus.root.children[i]); node.transform.column[3]={i*0.02,0,0};
    group.children.push_back(std::move(node));
  }
  auto edited=group.children.back().id;
  corpus.root.children.erase(corpus.root.children.begin(),corpus.root.children.begin()+33);
  corpus.root.children.insert(corpus.root.children.begin(),std::move(group));
  debug("CSG runtime benchmark protocol 1: brushes=1000 neighbors=32 max_input_faces=6 warmup=3 measured=10 atlas=1024 sample=0.1 source=%llu edits=Y(frame*0.01m)",csg::fingerprint(corpus.root));
  debug("CSG runtime benchmark backend: %s",d3d::get_driver_name());
  struct State
  {
    ecs::EntityId root;
    csg::Document original,corpus;
    csg::Id edited;
    int frame=0;
    double worst=0;
    ~State() {
      if(csg::getSceneDocument(root)) {
        csg::Diagnostics errors;
        if(!csg::updateScene(root,std::move(original),errors)) logerr("CSG runtime benchmark restore FAILED");
      }
    }
  };
  struct Step final : DelayedAction
  {
    std::shared_ptr<State> state;
    unsigned due;
    Step(std::shared_ptr<State> s,unsigned frame):state(std::move(s)),due(frame) {}
    bool precondition() override { return !csg::getSceneDocument(state->root) || unsigned(dagor_frame_no())>=due; }
    void performAction() override {
      auto &s=*state;
      if(!csg::getSceneDocument(s.root)) { logerr("CSG runtime benchmark cancelled: scene unloaded"); return; }
      if(s.frame && csg::getSceneRenderedRevision(s.root)<csg::getSceneResult(s.root)->revision) {
        logerr("CSG runtime full-pipeline fixture FAILED: previous revision was not consumed by the main render pass"); return;
      }
      if(s.frame==13) {
        debug("CSG runtime viewport revisions PASS: every warmup/measured revision reached the main opaque pass");
        debug("CSG runtime full-pipeline fixture neighbors=32 worst %.3f ms; timing %s",s.worst,s.worst<=33 ? "PASS":"FAIL");
        flush_debug_file(); return;
      }
      auto start=std::chrono::steady_clock::now();
      s.corpus.find(s.edited)->transform.column[3].y=s.frame*0.01;
      csg::Diagnostics errors;
      if(!csg::updateScene(s.root,s.corpus,errors)) {
        for(const auto &error:errors) logerr("CSG runtime benchmark: node %llu face %llu: %s",error.node,error.face,error.message.c_str());
        logerr("CSG runtime full-pipeline fixture FAILED at frame %d",s.frame); return;
      }
      double ms=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
      if(s.frame>=3) s.worst=std::max(s.worst,ms);
      debug("CSG runtime full-pipeline frame %d: %.3f ms (warmup=%d) render_frame=%u",s.frame,ms,s.frame<3,unsigned(dagor_frame_no()));
      ++s.frame;
      add_delayed_action_buffered(new Step(state,unsigned(dagor_frame_no())+1));
    }
  };
  auto state=std::make_shared<State>(); state->root=root; state->original=std::move(original);
  state->corpus=std::move(corpus); state->edited=edited;
  add_delayed_action_buffered(new Step(std::move(state),unsigned(dagor_frame_no())+60));
  return true; // Scheduled; the final log, not this return, establishes a pass.
}



// Capture actual renderer output through the existing screenshot service. No
// desktop input or window capture is involved; this is an opt-in dev fixture.
void run_csg_surface_capture(ecs::EntityId root)
{
  struct State { ecs::EntityId root; TMatrix original; int step=0; };
  struct Step final : DelayedAction
  {
    std::shared_ptr<State> state;
    unsigned due;
    Step(std::shared_ptr<State> s,unsigned frame):state(std::move(s)),due(frame) {}
    bool precondition() override { return !csg::getSceneDocument(state->root) || dagor_frame_no()>=due; }
    void performAction() override {
      auto &s=*state; if(!csg::getSceneDocument(s.root)) return;
      auto capture=[](const char *name) {
        d3d::GpuAutoLock lock;
        screencap::set_comments("CSG renderer regression fixture; camera motion and GBuffer capture");
        screencap::make_screenshot(get_world_renderer()->getFinalTargetTex(),name);
      };
      if(s.step>=68) {
        const char *modes[]={"ssao","finalAO","preshadow","contactShadows","shadowCascades","reflectance","ssrStrength","baseColor"};
        int index=(s.step-68)/2;
        if(index==int(sizeof(modes)/sizeof(modes[0]))) {
          console::command("render.show_gbuffer");
          debug("CSG surface capture completed: normals, smoothness, lit still/moving/returned, AO/shadow/material buffers; inspect images before accepting shading");
          flush_debug_file();
          return;
        }
        if((s.step-68)%2) capture(String(0,"csg_%s",modes[index]));
        else console::command(String(0,"render.show_gbuffer %s",modes[index]));
        ++s.step; add_delayed_action_buffered(new Step(state,dagor_frame_no()+8)); return;
      }
      unsigned delay=8;
      switch(s.step) {
        case 0: s.original=get_cam_itm(); enable_free_camera(); set_cam_itm(s.original);
          console::command("render.show_gbuffer normal"); break;
        case 1: capture("csg_normal"); break;
        case 2: console::command("render.show_gbuffer smoothness"); break;
        case 3: capture("csg_smoothness"); break;
        case 4: console::command("render.show_gbuffer"); delay=120; break;
        case 5: capture("csg_lit_still"); break;
        case 66: set_cam_itm(s.original); delay=120; break;
        case 67: capture("csg_lit_returned"); break;
        default: {
          // A repeatable camera translation over sixty rendered frames.
          auto tm=s.original; float t=float(s.step-6)/59.0f;
          tm.setcol(3,s.original.getcol(3)+Point3(std::sin(t*3.14159265f),0,-0.5f*std::sin(t*3.14159265f)));
          set_cam_itm(tm); delay=1;
          if(s.step==35) capture("csg_lit_moving");
          break;
        }
      }
      ++s.step;
      add_delayed_action_buffered(new Step(state,dagor_frame_no()+delay));
    }
  };
  auto state=std::make_shared<State>(); state->root=root;
  add_delayed_action_buffered(new Step(std::move(state),dagor_frame_no()+120));
}
