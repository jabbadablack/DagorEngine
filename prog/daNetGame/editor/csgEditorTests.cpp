// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <csg/ecs.h>
#include <daECS/core/entityManager.h>
#include <daECS/core/componentTypes.h>
#include <daECS/core/utility/ecsRecreate.h>
#include <daEditorE/editorCommon/entityObj.h>
#include <daEditorE/editorCommon/entityEditor.h>
#include <daEditorE/editorCommon/inGameEditor.h>
#include <gamePhys/collision/collisionLib.h>
#include <ioSys/dag_dataBlock.h>
#include <debug/dag_debug.h>
#include <debug/dag_logSys.h>
#include <startup/dag_globalSettings.h>
#include <util/dag_delayedAction.h>
#include <osApiWrappers/dag_miscApi.h>
#include <memory>
#include <cmath>
#if DAGOR_DBGLEVEL > 0
void run_csg_editor_acceptance(ecs::EntityId root)
{
  struct Probe final : EntityObj {
    Probe(const char *name,ecs::EntityId entity):EntityObj(name,entity) {}
    std::unique_ptr<UndoRedoObject> captureUndo() { return std::make_unique<UndoMatrix>(this); }
  };
  struct State {
    ecs::EntityId root,level; csg::Document original; csg::Id brush=0,group=0;
    Ptr<Probe> object;
    Ptr<EntityObj> parent,rootObject;
    std::unique_ptr<ecs::Scene::EntityRecord> originalRecord;
    ecs::Object originalOverrides;
    bool hadOverrides=false,wasDirty=false;
    std::unique_ptr<UndoRedoObject> undo;
    TMatrix expected=TMatrix::IDENT;
    uint64_t revision=0; int step=0,waits=0;
    ~State() {
      if(csg::getSceneDocument(root)) { csg::Diagnostics errors; csg::updateScene(root,std::move(original),errors); }
      if(originalRecord && ecs::g_scenes) {
        auto &active=ecs::g_scenes->getActiveScene();
        if(auto *record=active.findEntityRecordForModify(level)) *record=*originalRecord;
        if(auto *record=active.getSceneRecordById(originalRecord->sceneId)) record->isDirty=wasDirty;
        if(hadOverrides) g_entity_mgr->set(level,ECS_HASH("csg__transform_overrides"),std::move(originalOverrides));
        else remove_sub_template_async(level,"csg_level_overrides");
      }
    }
  };
  struct Step final : DelayedAction {
    std::shared_ptr<State> state; unsigned due;
    Step(std::shared_ptr<State> s,unsigned frame):state(std::move(s)),due(frame) {}
    bool precondition() override { return !csg::getSceneDocument(state->root) || unsigned(dagor_frame_no())>=due; }
    void performAction() override {
      auto &s=*state; if(!csg::getSceneDocument(s.root)) return;
      auto fail=[](const char *message) { logerr("CSG F2 transform acceptance FAIL: %s",message); flush_debug_file(); };
      if(!s.object) {
        auto candidate=s.original; csg::Node group; group.name="F2 transform probe"; group.transform.column[3]={30,4,0};
        for(int i=0;i<2;++i) { csg::Node brush; brush.brush=csg::box({2,2,2}); brush.transform.column[3]={i*8.0,0,0}; group.children.push_back(std::move(brush)); }
        candidate.assignIds(group); s.group=group.id; s.brush=group.children.front().id;
        candidate.root.children.push_back(std::move(group)); csg::Diagnostics errors;
        if(!csg::updateScene(s.root,std::move(candidate),errors)) { fail("probe creation"); return; }
        s.object=new Probe("CSG brush",csg::getSourceEntity(s.root,s.brush));
        s.parent=new EntityObj("CSG group",csg::getSourceEntity(s.root,s.group));
        s.rootObject=new EntityObj("CSG root",s.root);
        s.object->selectObject(); s.parent->selectObject(); s.rootObject->selectObject();
      } else {
        auto revision=csg::getSceneResult(s.root)->revision;
        const bool rejected=s.step==8;
        if((!rejected && (revision<=s.revision || csg::getSceneRenderedRevision(s.root)<revision)) ||
           (rejected && !*g_entity_mgr->getOr(s.object->getEid(),ECS_HASH("csg__edit_error"),""))) {
          if(++s.waits>120) { fail("transform did not reach the shared publisher"); return; }
          add_delayed_action_buffered(new Step(state,unsigned(dagor_frame_no())+1)); return;
        }
        s.waits=0; s.object->update(0); s.parent->update(0);
        const auto actual=s.object->getWtm();
        for(int axis=0;axis<4;++axis) if(lengthSq(actual.getcol(axis)-s.expected.getcol(axis))>1e-7f) { fail("accepted source transform differs from the native gizmo"); return; }
        if(rejected && revision!=s.revision) { fail("invalid scale changed the accepted revision"); return; }
        Point3 from=actual*Point3(0,0,-3),to=actual.getcol(3),direction=normalize(to-from);
        float distance=length(to-from); dacoll::ShapeQueryOutput hit;
        if(!dacoll::traceray_normalized(from,direction,distance,nullptr,nullptr) ||
           !dacoll::sphere_cast_ex(from,to,0.05f,hit,-1,{})) { fail("rendered transform and Jolt collision disagree"); return; }
        BBox3 bounds;
        if(!s.object->getWorldBox(bounds) || !(bounds & actual.getcol(3))) { fail("native selection/focus bounds"); return; }
        if(rejected) {
          const auto *record=ecs::g_scenes->getActiveScene().findEntityRecord(s.level);
          if(!record || record->templateName.find("csg_level_overrides")==eastl::string::npos) { fail("native scene save did not retain the override template"); return; }
          if(const char *path=dgs_get_settings()->getBlockByNameEx("debug")->getStr("csgEditorSavePath",nullptr)) {
            init_entity_object_editor(); auto *editor=get_entity_obj_editor();
            record=ecs::g_scenes->getActiveScene().findEntityRecord(s.level);
            auto *owner=record ? ecs::g_scenes->getActiveScene().getSceneRecordById(record->sceneId):nullptr;
            DataBlock saved;
            if(!editor || !owner || !EntityObjEditor::writeSceneToBlk(saved,*owner,*editor)) { fail("native scene-save output"); return; }
            // This copy deliberately moves the whole room. Its reload check
            // replaces the fixture's original fixed-world-position assertions.
            for(int i=0;i<saved.blockCount();++i) if(!strcmp(saved.getBlock(i)->getStr("_template",""),"csg_acceptance_camera"))
              saved.getBlock(i)->setBool("csg_acceptance__done",true);
            if(!saved.saveToTextFile(path)) { fail("native scene-save output"); return; }
            debug("CSG F2 scene-save acceptance PASS: %s",path);
          }
          debug("CSG F2 transform acceptance PASS: native selection bounds, move/rotate/scale, undo/redo, group/root movement, scene overrides, render/Jolt revisions and invalid-scale rollback"); flush_debug_file(); return;
        }
      }
      s.revision=csg::getSceneResult(s.root)->revision;
      switch(s.step) {
        case 0: s.object->moveObject(Point3(3,0,0),IDaEditor4Engine::BASIS_world); break;
        case 1: s.object->rotateObject(Point3(0,0.4f,0),s.object->getPos(),IDaEditor4Engine::BASIS_world); break;
        case 2: s.undo=s.object->captureUndo();
          s.object->scaleObject(Point3(1.5f,0.75f,1.25f),s.object->getPos(),IDaEditor4Engine::BASIS_local); break;
        case 3: s.undo->restore(true); break;
        case 4: s.undo->redo(); break;
        case 5: s.expected=s.object->getWtm(); s.expected.setcol(3,s.expected.getcol(3)+Point3(0,2,1));
          s.parent->moveObject(Point3(0,2,1),IDaEditor4Engine::BASIS_world); break;
        case 6: s.expected=s.object->getWtm(); s.expected.setcol(3,s.expected.getcol(3)+Point3(3,0,0));
          s.rootObject->moveObject(Point3(3,0,0),IDaEditor4Engine::BASIS_world); break;
        case 7: s.expected=s.object->getWtm(); { auto invalid=s.expected; invalid.setcol(0,Point3(0,0,0)); s.object->setWtm(invalid); } break;
      }
      if(s.step<5) s.expected=s.object->getWtm();
      ++s.step; add_delayed_action_buffered(new Step(state,unsigned(dagor_frame_no())+2));
    }
  };
  auto state=std::make_shared<State>(); state->root=root; state->original=*csg::getSceneDocument(root);
  state->level=g_entity_mgr->getOr(root,ECS_HASH("csg__level"),ecs::INVALID_ENTITY_ID);
  if(const auto *record=ecs::g_scenes->getActiveScene().findEntityRecord(state->level)) {
    state->originalRecord=std::make_unique<ecs::Scene::EntityRecord>(*record);
    if(const auto *owner=ecs::g_scenes->getActiveScene().getSceneRecordById(record->sceneId)) state->wasDirty=owner->isDirty;
  }
  if(const auto *overrides=g_entity_mgr->getNullable<ecs::Object>(state->level,ECS_HASH("csg__transform_overrides"))) {
    state->hadOverrides=true; state->originalOverrides=*overrides;
  }
  add_delayed_action_buffered(new Step(std::move(state),unsigned(dagor_frame_no())+60));
}

void run_csg_editor_reload_acceptance(ecs::EntityId root)
{
  struct Check final : DelayedAction {
    ecs::EntityId root; unsigned due;
    Check(ecs::EntityId entity):root(entity),due(unsigned(dagor_frame_no())+60) {}
    bool precondition() override { return !csg::getSceneDocument(root) || unsigned(dagor_frame_no())>=due; }
    void performAction() override {
      auto *document=csg::getSceneDocument(root); if(!document) return;
      float distance=10; dacoll::ShapeQueryOutput hit;
      bool ok=std::abs(document->root.transform.column[3].x-3)<1e-5 &&
        csg::getSceneRenderedRevision(root)>=csg::getSceneResult(root)->revision &&
        dacoll::traceray_normalized(Point3(3,1,0),Point3(1,0,0),distance,nullptr,nullptr) && std::abs(distance-3.75f)<0.02f &&
        dacoll::sphere_cast_ex(Point3(3,1,0),Point3(8,1,0),0.1f,hit,-1,{});
      if(ok) debug("CSG F2 save/reload acceptance PASS: source transform, rendered revision and Jolt collision restored from native scene overrides");
      else logerr("CSG F2 save/reload acceptance FAIL");
      flush_debug_file();
    }
  }; add_delayed_action_buffered(new Check(root));
}
#endif
