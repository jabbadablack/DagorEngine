// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "main/csgEntities.h"
#include <debug/dag_debug.h>
#include <csg/ecs.h>
bool create_csg_runtime_scene(const DataBlock &,ecs::EntityId,dag::ConstSpan<ecs::EntityId>)
{
  logerr("Runtime CSG scene publication requires the client renderer");
  return false;
}
void destroy_csg_runtime_scene(ecs::EntityId) {}
const csg::Document *csg::getSceneDocument(ecs::EntityId) { return nullptr; }
const csg::Result *csg::getSceneResult(ecs::EntityId) { return nullptr; }
uint64_t csg::getSceneRenderedRevision(ecs::EntityId) { return 0; }
ecs::EntityId csg::getSourceEntity(ecs::EntityId,Id) { return ecs::INVALID_ENTITY_ID; }
bool csg::updateScene(ecs::EntityId,Document &&,Diagnostics &errors)
{
  errors.push_back({Code::InvalidResult,0,0,"Runtime CSG scene publication requires the client renderer"});
  return false;
}
bool csg::updateScene(ecs::EntityId source,const Document &candidate,Diagnostics &errors)
{
  Document copy=candidate; return updateScene(source,std::move(copy),errors);
}
