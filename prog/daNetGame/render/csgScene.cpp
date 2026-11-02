// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "main/csgEntities.h"
#include "render/renderer.h"
#include <csg/scene.h>
#include <csg/document.h>
#include <csg/ecs.h>
#include <daECS/core/entityManager.h>
#include <daECS/core/componentTypes.h>
#include <daECS/core/utility/ecsRecreate.h>
#include <daECS/scene/scene.h>
#include <3d/dag_materialData.h>
#include <ioSys/dag_dataBlock.h>
#include <ioSys/dag_memIo.h>
#include <osApiWrappers/dag_miscApi.h>
#include <util/dag_delayedAction.h>
#include <startup/dag_globalSettings.h>
#include <util/dag_console.h>
#include <debug/dag_debug.h>
#include <gui/dag_visualLog.h>
#include <math/dag_bounds3.h>
#include <map>
#include <set>
#include <functional>
#include <cmath>
#include <cstring>
#include <chrono>
#include <memory/dag_dbgMem.h>
bool run_csg_runtime_acceptance(ecs::EntityId root);
void run_csg_runtime_frame_acceptance(ecs::EntityId root);
bool run_csg_runtime_benchmark(ecs::EntityId root);
void run_csg_surface_capture(ecs::EntityId root);
void run_csg_editor_acceptance(ecs::EntityId root);
void run_csg_editor_reload_acceptance(ecs::EntityId root);

namespace
{
struct SourceRecord
{
  ecs::EntityId entity,parent;
  uint64_t hash=0,nextId=0;
  std::string name;
  TMatrix world=TMatrix::IDENT;
  BBox3 localBounds;
  int order=0;
};
struct LiveScene
{
  std::unique_ptr<csg::Scene> scene;
  std::map<csg::Id,SourceRecord> sources;
  ecs::EntityId level;
  csg::Id rootId=0;
  bool updating=false;
  bool transformUpdateQueued=false;
  std::map<csg::Id,TMatrix> pendingTransforms;
  std::set<csg::Id> pendingSaveTransforms;
};
std::map<ecs::EntityId,std::unique_ptr<LiveScene>> runtimeScenes;
LiveScene *findScene(ecs::EntityId source)
{
  for(int depth=0;depth<=128 && g_entity_mgr->doesEntityExist(source);++depth) {
    auto found=runtimeScenes.find(source); if(found!=runtimeScenes.end()) return found->second.get();
    source=g_entity_mgr->getOr(source,ECS_HASH("csg__parent"),ecs::INVALID_ENTITY_ID);
  }
  return nullptr;
}
std::string transformOverrideKey(csg::Id root,csg::Id node)
{ return "r"+std::to_string(root)+"_n"+std::to_string(node); }
}
bool create_csg_runtime_scene(const DataBlock &source,ecs::EntityId root,dag::ConstSpan<ecs::EntityId> sources)
{
  csg::Document document; csg::Diagnostics errors;
  if(!csg::loadDocument(source,document,errors)) return false;
  std::vector<csg::SceneMaterial> materials;
  std::vector<Ptr<MaterialData>> owners;
  const auto *palette=source.getBlockByName("runtimeMaterials"); if(!palette) return false;
  for(int i=0;i<palette->blockCount();++i) {
    const auto &entry=*palette->getBlock(i); Ptr<MaterialData> data=new MaterialData;
    data->matName=entry.getStr("name",""); data->className=entry.getStr("class","");
    data->matScript=entry.getStr("script",""); data->flags=entry.getInt("flags",0);
    auto color=[&](const char *name) { auto c=entry.getPoint4(name,Point4(0,0,0,0)); return Color4(c.x,c.y,c.z,c.w); };
    data->mat.diff=color("diffuse"); data->mat.amb=color("ambient"); data->mat.spec=color("specular"); data->mat.emis=color("emissive");
    data->mat.power=entry.getReal("power",0);
    for(int j=0;j<entry.blockCount();++j) {
      const auto &texture=*entry.getBlock(j); int slot=texture.getInt("slot",-1);
      if(slot<0 || slot>=MAXMATTEXNUM) return false;
      auto id=get_managed_texture_id(texture.getStr("managedName","")); if(id==BAD_TEXTUREID) return false;
      data->mtex[slot]=id;
      debug("Runtime CSG material '%s' texture slot %d: %s",data->matName.str(),slot,get_managed_texture_name(id));
    }
    materials.push_back({entry.getStr("name",""),data}); owners.push_back(data);
  }
  csg::SceneSettings settings;
  settings.lightmapSize=source.getInt("lightmapSize",1024); settings.lightmapSampleSize=source.getReal("lightmapSampleSize",0.1f);
  auto live=std::make_unique<LiveScene>(); live->scene=std::make_unique<csg::Scene>(settings,materials);
  live->level=g_entity_mgr->getOr(root,ECS_HASH("csg__level"),ecs::INVALID_ENTITY_ID); live->rootId=document.root.id;
  if(const auto *overrides=g_entity_mgr->getNullable<ecs::Object>(live->level,ECS_HASH("csg__transform_overrides"))) {
    std::function<void(csg::Node &)> apply=[&](csg::Node &node) {
      auto key=transformOverrideKey(document.root.id,node.id);
      if(const auto *tm=overrides->getNullable<TMatrix>(ECS_HASH_SLOW(key.c_str())))
        for(int axis=0;axis<4;++axis) { auto p=tm->getcol(axis); node.transform.column[axis]={p.x,p.y,p.z}; }
      for(auto &child:node.children) apply(child);
    }; apply(document.root);
  }
  for(auto entity:sources) {
    SourceRecord record; record.entity=entity;
    auto id=g_entity_mgr->getOr(entity,ECS_HASH("csg__id"),int64_t(0)); live->sources.emplace(csg::Id(id),std::move(record));
  }
  runtimeScenes.emplace(root,std::move(live));
  if(!csg::updateScene(root,std::move(document),errors)) {
    for(const auto &error:errors) logerr("Runtime CSG: node %llu face %llu: %s",error.node,error.face,error.message.c_str());
    runtimeScenes.erase(root);
    return false;
  }
  debug("Runtime CSG scene published: rendering, lightmap UVs and world collision revision 1");
#if DAGOR_DBGLEVEL > 0
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgEditorAcceptance",false))
    run_csg_editor_acceptance(root);
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgEditorReloadAcceptance",false))
    run_csg_editor_reload_acceptance(root);
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgSurfaceCapture",false))
    run_csg_surface_capture(root);
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeAcceptance",false))
    if(run_csg_runtime_acceptance(root)) run_csg_runtime_frame_acceptance(root);
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeBenchmark",false)) {
    if(settings.lightmapSize==1024 && settings.lightmapSampleSize==0.1f) run_csg_runtime_benchmark(root);
    else logerr("CSG runtime benchmark FAILED: requires the frozen 1024 atlas and 0.1 sample size");
  }
  if(const char *view=dgs_get_settings()->getBlockByNameEx("debug")->getStr("csgGbuffer",nullptr)) {
    String command(0,"render.show_gbuffer %s",view);
    delayed_call([command] { console::command(command); });
  }
  if(const char *text=dgs_get_settings()->getBlockByNameEx("debug")->getStr("csgConsole",nullptr)) {
    String command(text); delayed_call([command] { console::command(command); });
  }
#endif
  return true;
}
void destroy_csg_runtime_scene(ecs::EntityId root)
{
  auto found=runtimeScenes.find(root); if(found==runtimeScenes.end()) return;
  for(const auto &[id,source]:found->second->sources)
    if(g_entity_mgr->doesEntityExist(source.entity)) g_entity_mgr->destroyEntity(source.entity);
  runtimeScenes.erase(found);
}
const csg::Document *csg::getSceneDocument(ecs::EntityId source)
{
  auto *live=findScene(source); return live ? &live->scene->document():nullptr;
}
const csg::Result *csg::getSceneResult(ecs::EntityId source)
{
  auto *live=findScene(source); return live ? &live->scene->result():nullptr;
}
uint64_t csg::getSceneRenderedRevision(ecs::EntityId source)
{
  auto *live=findScene(source); return live ? live->scene->lastRenderedRevision():0;
}
ecs::EntityId csg::getSourceEntity(ecs::EntityId source,Id id)
{
  auto *live=findScene(source); if(!live) return ecs::INVALID_ENTITY_ID;
  auto found=live->sources.find(id); return found!=live->sources.end() ? found->second.entity:ecs::INVALID_ENTITY_ID;
}
bool csg::updateScene(ecs::EntityId source,const Document &candidate,Diagnostics &errors)
{
  DagDbgMem::ForcedProfileCallStackRAII allocationProfile;
  Document copy=candidate;
  return updateScene(source,std::move(copy),errors);
}
bool csg::updateScene(ecs::EntityId source,Document &&candidate,Diagnostics &errors)
{
  // Keep debug allocation accounting, attributing this transaction's temporary
  // allocations to its caller instead of walking the same stack per corner.
  DagDbgMem::ForcedProfileCallStackRAII allocationProfile;
  auto start=std::chrono::steady_clock::now();
  auto fail=[&](Id node,const char *message) { errors.push_back({Code::InvalidDocument,node,0,message}); return false; };
  if(!is_main_thread()) return fail(0,"Runtime CSG updates require the main thread");
  auto *live=findScene(source); if(!live) return fail(0,"Entity is not in a runtime-editable CSG scene");
  if(live->updating) return fail(0,"Reentrant runtime CSG scene update");
  live->updating=true;
  struct UpdateGuard { bool &updating; ~UpdateGuard(){updating=false;} } updateGuard{live->updating};
  if(candidate.root.id!=live->rootId) return fail(candidate.root.id,"A runtime scene's root source ID cannot change");
  if(candidate.nextId>uint64_t(INT64_MAX)) return fail(candidate.root.id,"Runtime source IDs exceed the ECS integer range");
  candidate.runtimeEditable=true;
  struct Pending { ecs::EntityId entity; ecs::ComponentsInitializer attributes; };
  std::vector<Pending> pending;
  std::vector<ecs::EntityId> created;
  struct Rollback
  {
    std::vector<ecs::EntityId> &entities; bool accepted=false;
    ~Rollback() { if(!accepted) for(auto entity:entities) g_entity_mgr->destroyEntity(entity); }
  } rollback{created};
  std::map<Id,SourceRecord> next;
  size_t count=0;
  std::function<bool(const Node &,ecs::EntityId,Id,const TMatrix &,int,unsigned)> visit;
  visit=[&](const Node &node,ecs::EntityId parent,Id parentId,const TMatrix &parentWorld,int order,unsigned depth) {
    if(depth>128 || ++count>100000 || !node.id || node.id>uint64_t(INT64_MAX) || next.count(node.id))
      return fail(node.id,"Invalid or duplicate runtime source identity/hierarchy");
    TMatrix local;
    for(int i=0;i<4;++i) {
      const auto &p=node.transform.column[i];
      if(!finite(p) || !finite(Vec{double(float(p.x)),double(float(p.y)),double(float(p.z))}))
        return fail(node.id,"Runtime source transform is not finite");
      local.setcol(i,Point3(float(p.x),float(p.y),float(p.z)));
    }
    SourceRecord record; record.parent=parent; record.world=parentWorld*local;
    for(int i=0;i<4;++i) {
      auto p=record.world.getcol(i); if(!finite(Vec{p.x,p.y,p.z})) return fail(node.id,"Runtime world transform overflow");
    }
    record.hash=fingerprint(node,false); record.name=node.name; record.order=order; record.nextId=parentId ? 0:candidate.nextId;
    auto old=live->sources.find(node.id);
    bool changed=old==live->sources.end();
    if(!changed) {
      const auto &previous=old->second; record.entity=previous.entity;
      if(!g_entity_mgr->doesEntityExist(record.entity)) return fail(node.id,"A CSG source entity was removed outside its scene");
      changed=!parentId || record.hash!=previous.hash || record.name!=previous.name || record.parent!=previous.parent ||
        record.order!=previous.order || record.nextId!=previous.nextId || std::memcmp(&record.world,&previous.world,sizeof(TMatrix));
    }
    BBox3 bounds;
    if(node.parametric && old!=live->sources.end() && record.hash==old->second.hash)
      bounds=old->second.localBounds;
    else {
      csg::Mesh generated; const auto *mesh=&node.brush;
      if(node.parametric) {
        if(!generateExtrusion(node.extrusion,generated,errors)) return false;
        mesh=&generated;
      }
      for(const auto &p:mesh->vertices) {
        Vec rounded{double(float(p.x)),double(float(p.y)),double(float(p.z))};
        if(!finite(rounded)) return fail(node.id,"CSG editor bounds are not finite");
        bounds+=Point3(float(p.x),float(p.y),float(p.z));
      }
    }
    const size_t pendingIndex=pending.size();
    if(changed) {
      DataBlock block; saveSourceNode(node,block); DynamicMemGeneralSaveCB text(tmpmem);
      if(!block.saveToTextStreamCompact(text)) return fail(node.id,"Runtime source serialization failed");
      ecs::ComponentsInitializer attrs;
      attrs[ECS_HASH("transform")]=record.world; attrs[ECS_HASH("csg__local_transform")]=local;
      attrs[ECS_HASH("csg__id")]=int64_t(node.id); attrs[ECS_HASH("csg__parent_id")]=int64_t(parentId);
      attrs[ECS_HASH("csg__next_id")]=int64_t(record.nextId); attrs[ECS_HASH("csg__parent")]=parent;
      attrs[ECS_HASH("csg__level")]=live->level; attrs[ECS_HASH("csg__operation")]=int(node.operation);
      attrs[ECS_HASH("csg__enabled")]=node.visible; attrs[ECS_HASH("csg__parametric")]=node.parametric;
      attrs[ECS_HASH("csg__name")]=ecs::string(node.name.c_str()); attrs[ECS_HASH("csg__order")]=order;
      attrs[ECS_HASH("editor__name")]=ecs::string(node.name.empty() ? "CSG source":node.name.c_str());
      attrs[ECS_HASH("csg__source_blk")]=ecs::string(reinterpret_cast<const char *>(text.data()),size_t(text.size()));
      if(old==live->sources.end()) {
        auto initial=attrs; initial[ECS_HASH("csg__published")]=false; initial[ECS_HASH("editableObj")]=false;
        record.entity=g_entity_mgr->createEntitySync("csg_source",eastl::move(initial));
        if(record.entity==ecs::INVALID_ENTITY_ID) return fail(node.id,"Runtime source entity creation failed");
        created.push_back(record.entity);
      }
      attrs[ECS_HASH("csg__published")]=true; attrs[ECS_HASH("editableObj")]=true;
      attrs[ECS_HASH("csg__revision")]=int64_t(live->scene->result().revision+1);
      attrs[ECS_HASH("csg__edit_error")]=ecs::string();
      pending.push_back({record.entity,eastl::move(attrs)});
    }
    next.emplace(node.id,record);
    for(size_t i=0;i<node.children.size();++i)
      if(!visit(node.children[i],record.entity,node.id,record.world,int(i),depth+1)) return false;
    for(const auto &child:node.children) {
      const auto &childBounds=next.at(child.id).localBounds;
      for(unsigned corner=0;corner<8;++corner) {
        Vec p{childBounds[(corner&1)!=0].x,childBounds[(corner&2)!=0].y,childBounds[(corner&4)!=0].z};
        auto q=child.transform.point(p); bounds+=Point3(float(q.x),float(q.y),float(q.z));
      }
    }
    if(bounds.isempty()) bounds=BBox3(Point3(-0.1f,-0.1f,-0.1f),Point3(0.1f,0.1f,0.1f));
    next.at(node.id).localBounds=bounds;
    if(changed) {
      pending[pendingIndex].attributes[ECS_HASH("custom_edit_box__min")]=bounds[0];
      pending[pendingIndex].attributes[ECS_HASH("custom_edit_box__max")]=bounds[1];
    } else if(bounds[0]!=old->second.localBounds[0] || bounds[1]!=old->second.localBounds[1]) {
      ecs::ComponentsInitializer attrs;
      attrs[ECS_HASH("custom_edit_box__min")]=bounds[0]; attrs[ECS_HASH("custom_edit_box__max")]=bounds[1];
      pending.push_back({record.entity,eastl::move(attrs)});
    }
    return true;
  };
  if(!visit(candidate.root,ecs::INVALID_ENTITY_ID,0,TMatrix::IDENT,0,0)) return false;
  double metadataMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
  if(!live->scene->update(std::move(candidate),errors)) return false;
  auto publicationEnd=std::chrono::steady_clock::now();
  for(auto &change:pending) for(auto &attribute:change.attributes)
    g_entity_mgr->set(change.entity,ecs::HashedConstString{"CSG source component",attribute.name},eastl::move(attribute.second));
  for(const auto &[id,previous]:live->sources) if(!next.count(id)) g_entity_mgr->destroyEntity(previous.entity);
  live->sources.swap(next); rollback.accepted=true;
  const auto &changed=live->scene->lastChangedBounds();
  if(!changed.isempty()) if(auto *renderer=get_world_renderer()) {
    renderer->shadowsInvalidate(changed);
    renderer->invalidateGI(changed);
  }
  if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeBenchmark",false))
    debug("CSG runtime ECS: metadata %.3f finalize %.3f ms",metadataMs,
      std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-publicationEnd).count());
  return true;
}

void queue_csg_source_transform_update(ecs::EntityId source,const TMatrix &world,bool saveToScene)
{
  auto *live=findScene(source); if(!live || live->updating) return;
  auto id=csg::Id(g_entity_mgr->getOr(source,ECS_HASH("csg__id"),int64_t(0)));
  auto record=live->sources.find(id);
  if(record==live->sources.end() || record->second.entity!=source) return;
  if(saveToScene) live->pendingSaveTransforms.insert(id);
  if(world==record->second.world && !live->pendingSaveTransforms.count(id)) { live->pendingTransforms.erase(id); return; }
  live->pendingTransforms[id]=world;
  if(live->transformUpdateQueued) return;
  live->transformUpdateQueued=true;
  const auto root=live->sources.at(live->rootId).entity;
  delayed_call([root] {
    auto found=runtimeScenes.find(root); if(found==runtimeScenes.end()) return;
    auto &scene=*found->second;
    auto requested=std::move(scene.pendingTransforms); scene.pendingTransforms.clear();
    auto saveIds=std::move(scene.pendingSaveTransforms); scene.pendingSaveTransforms.clear();
    scene.transformUpdateQueued=false;
    if(requested.empty()) return;
    auto candidate=scene.scene->document(); csg::Diagnostics errors;
    std::function<bool(csg::Node &,const csg::Transform &)> apply;
    apply=[&](csg::Node &node,const csg::Transform &parent) {
      if(auto edit=requested.find(node.id);edit!=requested.end()) {
        const auto &desired=edit->second;
        double determinant=parent.determinant();
        if(!csg::finite({determinant,0,0}) || std::abs(determinant)<1e-12) {
          errors.push_back({csg::Code::InvalidDocument,node.id,0,"Cannot transform a CSG source beneath a singular parent"}); return false;
        }
        auto point=[](const Point3 &p) { return csg::Vec{p.x,p.y,p.z}; };
        const auto origin=point(desired.getcol(3));
        node.transform.column[3]=parent.inversePoint(origin);
        for(int axis=0;axis<3;++axis)
          node.transform.column[axis]=parent.inversePoint(origin+point(desired.getcol(axis)))-node.transform.column[3];
      }
      csg::Transform world;
      for(int axis=0;axis<3;++axis) world.column[axis]=parent.vector(node.transform.column[axis]);
      world.column[3]=parent.point(node.transform.column[3]);
      for(auto &child:node.children) if(!apply(child,world)) return false;
      return true;
    };
    bool valid=apply(candidate.root,{});
    ecs::Object overrides;
    ecs::ComponentsList savedComponents;
    eastl::string savedTemplate;
    if(valid && !saveIds.empty()) {
      auto *record=ecs::g_scenes ? ecs::g_scenes->getActiveScene().findEntityRecord(scene.level):nullptr;
      if(!record) {
        errors.push_back({csg::Code::InvalidDocument,scene.rootId,0,"The CSG level is not part of the editable scene"}); valid=false;
      } else {
        if(const auto *current=g_entity_mgr->getNullable<ecs::Object>(scene.level,ECS_HASH("csg__transform_overrides"))) overrides=*current;
        // Include edits already staged while the level's native subtemplate is
        // being added asynchronously. Normal scene saves can run immediately.
        for(const auto &component:record->clist) if(component.first=="csg__transform_overrides")
          if(const auto *staged=component.second.getNullable<ecs::Object>()) overrides=*staged;
        for(auto id:saveIds) if(const auto *node=candidate.find(id)) {
          TMatrix local;
          for(int axis=0;axis<4;++axis) { auto p=node->transform.column[axis]; local.setcol(axis,Point3(float(p.x),float(p.y),float(p.z))); }
          auto key=transformOverrideKey(scene.rootId,id); overrides.addMember(key.c_str(),local);
        }
        savedComponents=record->clist;
        auto component=eastl::find_if(savedComponents.begin(),savedComponents.end(),[](const auto &value) { return value.first=="csg__transform_overrides"; });
        if(component==savedComponents.end()) savedComponents.emplace_back("csg__transform_overrides",ecs::ChildComponent(overrides));
        else component->second=ecs::ChildComponent(overrides);
        savedTemplate=add_sub_template_name(record->templateName.c_str(),"csg_level_overrides").c_str();
      }
    }
    if(valid && csg::updateScene(root,std::move(candidate),errors)) {
      if(!saveIds.empty()) {
        auto &active=ecs::g_scenes->getActiveScene(); auto *record=active.findEntityRecordForModify(scene.level);
        record->clist=std::move(savedComponents); record->templateName=std::move(savedTemplate);
        active.setNewChangesApplied(record->sceneId);
        if(g_entity_mgr->has(scene.level,ECS_HASH("csg__transform_overrides")))
          g_entity_mgr->set(scene.level,ECS_HASH("csg__transform_overrides"),std::move(overrides));
        else {
          ecs::ComponentsInitializer attrs; attrs[ECS_HASH("csg__transform_overrides")]=std::move(overrides);
          add_sub_template_async(scene.level,"csg_level_overrides",eastl::move(attrs));
        }
      }
      return;
    }
    const std::string message=errors.empty() ? "CSG transform rejected":("CSG transform rejected: "+errors.front().message);
    for(const auto &[id,desired]:requested) {
      (void)desired;
      auto old=scene.sources.find(id); if(old==scene.sources.end() || !g_entity_mgr->doesEntityExist(old->second.entity)) continue;
      g_entity_mgr->set(old->second.entity,ECS_HASH("transform"),old->second.world);
      g_entity_mgr->set(old->second.entity,ECS_HASH("csg__edit_error"),ecs::string(message.c_str()));
    }
    visuallog::logmsg(message.c_str());
    logwarn("%s",message.c_str());
  });
}
