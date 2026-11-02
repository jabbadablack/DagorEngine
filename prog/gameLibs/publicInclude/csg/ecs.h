// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <csg/geometry.h>
#include <daECS/core/entityId.h>
namespace csg
{
// Any source entity in the hierarchy addresses its owning runtime scene.
const Document *getSceneDocument(ecs::EntityId source);
const Result *getSceneResult(ecs::EntityId source);
// Last accepted revision consumed by the main opaque render pass.
uint64_t getSceneRenderedRevision(ecs::EntityId source);
ecs::EntityId getSourceEntity(ecs::EntityId scene,Id source_id);
// On success the engine publishes geometry, UVs, collision and source entities.
// Existing source IDs retain their ECS identities; failed edits retain everything.
bool updateScene(ecs::EntityId source,Document &&candidate,Diagnostics &errors);
bool updateScene(ecs::EntityId source,const Document &candidate,Diagnostics &errors);
}
