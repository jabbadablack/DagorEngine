// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "csgEntities.h"
#include <daECS/core/entityManager.h>
#include <daECS/core/componentTypes.h>
#include <daECS/core/template.h>
#include <ioSys/dag_dataBlock.h>
#include <ioSys/dag_memIo.h>
#include <debug/dag_debug.h>
#include <functional>
#include <locale>
#include <sstream>
#include <cmath>

void register_csg_templates(ecs::EntityManager &manager)
{
  if(!manager.getTemplateDB().getTemplateByName("csg_level_overrides")) {
    ecs::ComponentsMap map; map[ECS_HASH("csg__transform_overrides")]=ecs::Object();
    manager.addTemplate(ecs::Template("csg_level_overrides",eastl::move(map),ecs::Template::component_set(),
      ecs::Template::component_set(),ecs::Template::component_set(),false));
  }
  if(!manager.getTemplateDB().getTemplateByName("csg_source")) {
    ecs::ComponentsMap map;
    map[ECS_HASH("csg_source")] = ecs::Tag();
    map[ECS_HASH("transform")] = TMatrix::IDENT;
    map[ECS_HASH("csg__local_transform")] = TMatrix::IDENT;
    map[ECS_HASH("csg__id")] = int64_t(0);
    map[ECS_HASH("csg__parent_id")] = int64_t(0);
    map[ECS_HASH("csg__next_id")] = int64_t(0);
    map[ECS_HASH("csg__parent")] = ecs::INVALID_ENTITY_ID;
    map[ECS_HASH("csg__level")] = ecs::INVALID_ENTITY_ID;
    map[ECS_HASH("csg__operation")] = 0;
    map[ECS_HASH("csg__enabled")] = true;
    map[ECS_HASH("csg__parametric")] = false;
    map[ECS_HASH("csg__name")] = ecs::string();
    map[ECS_HASH("editor__name")] = ecs::string();
    map[ECS_HASH("csg__source_blk")] = ecs::string();
    map[ECS_HASH("csg__order")] = 0;
    map[ECS_HASH("csg__revision")] = int64_t(0);
    map[ECS_HASH("csg__published")] = true;
    map[ECS_HASH("csg__edit_error")] = ecs::string();
    map[ECS_HASH("custom_edit_box__min")] = Point3(-0.1f,-0.1f,-0.1f);
    map[ECS_HASH("custom_edit_box__max")] = Point3(0.1f,0.1f,0.1f);
    map[ECS_HASH("editableObj")] = true;
    ecs::Template::component_set tracked; tracked.insert(ECS_HASH("transform").hash);
    manager.addTemplate(ecs::Template("csg_source",eastl::move(map),eastl::move(tracked),
      ecs::Template::component_set(),ecs::Template::component_set(),false));
  }
}
bool create_csg_source_entities(const DataBlock &document,ecs::EntityId level,Tab<ecs::EntityId> &created)
{
  int version=document.getInt("version",0);
  const auto *root=document.getBlockByName("root");
  if(version<1 || version>2 || !root) { logerr("Invalid runtime CSG source document"); return false; }
  register_csg_templates(*g_entity_mgr);
  int start=created.size(),cutters=0,groups=0; size_t visited=0;
  std::function<bool(const DataBlock &,ecs::EntityId,int64_t,const TMatrix &,unsigned)> visit;
  visit=[&](const DataBlock &node,ecs::EntityId parent,int64_t parentId,const TMatrix &parentTm,unsigned depth) {
    if(depth>128 || ++visited>100000) return false;
    TMatrix local=TMatrix::IDENT;
    const char *keys[]={"axisX","axisY","axisZ","origin"};
    for(int i=0;i<4;++i) if(const char *text=node.getStr(keys[i],nullptr)) {
      std::istringstream stream(text); stream.imbue(std::locale::classic()); double x,y,z;
      if(!(stream>>x>>y>>z) || !std::isfinite(x)||!std::isfinite(y)||!std::isfinite(z)) return false;
      stream>>std::ws; if(!stream.eof()) return false;
      local.setcol(i,Point3(float(x),float(y),float(z)));
    }
    auto id=node.getInt64("id",0); if(id<=0) return false;
    DataBlock source(node); while(source.removeBlock("node")) {} // This entity owns only its own source.
    DynamicMemGeneralSaveCB text(tmpmem); if(!source.saveToTextStreamCompact(text)) return false;
    ecs::ComponentsInitializer attrs;
    attrs[ECS_HASH("transform")]=parentTm*local;
    attrs[ECS_HASH("csg__local_transform")]=local;
    attrs[ECS_HASH("csg__id")]=int64_t(id);
    attrs[ECS_HASH("csg__parent_id")]=parentId;
    attrs[ECS_HASH("csg__next_id")]=int64_t(parentId ? 0:document.getInt64("nextId",0));
    attrs[ECS_HASH("csg__parent")]=parent;
    attrs[ECS_HASH("csg__level")]=level;
    attrs[ECS_HASH("csg__operation")]=node.getInt("operation",0);
    attrs[ECS_HASH("csg__enabled")]=node.getBool("visible",true);
    attrs[ECS_HASH("csg__parametric")]=node.getBlockByName("extrusion")!=nullptr;
    attrs[ECS_HASH("csg__name")]=ecs::string(node.getStr("name",""));
    attrs[ECS_HASH("editor__name")]=ecs::string(node.getStr("name","CSG source"));
    attrs[ECS_HASH("csg__source_blk")]=ecs::string(reinterpret_cast<const char *>(text.data()),size_t(text.size()));
    auto entity=g_entity_mgr->createEntitySync("csg_source",eastl::move(attrs));
    if(entity==ecs::INVALID_ENTITY_ID) return false;
    created.push_back(entity);
    if(node.getInt("operation",0)==1) ++cutters;
    if(!node.getBlockByName("extrusion") && node.getBlockByNameEx("brush")->blockCount()==0) ++groups;
    for(int i=0;i<node.blockCount();++i) if(!strcmp(node.getBlock(i)->getBlockName(),"node"))
      if(!visit(*node.getBlock(i),entity,id,parentTm*local,depth+1)) return false;
    return true;
  };
  if(!visit(*root,ecs::INVALID_ENTITY_ID,0,TMatrix::IDENT,0) ||
    (document.getBool("runtimeEditable",false) &&
      !create_csg_runtime_scene(document,created[start],{created.data()+start,size_t(created.size()-start)}))) {
    while(created.size()>start) { g_entity_mgr->destroyEntity(created.back()); created.pop_back(); }
    logerr("CSG source entity creation failed; partial hierarchy removed"); return false;
  }
  debug("CSG source entities created: %d (%d cutters, %d groups), stable IDs and source data retained",created.size()-start,cutters,groups);
  return true;
}
