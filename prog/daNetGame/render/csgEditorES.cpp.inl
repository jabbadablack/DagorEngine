// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "main/csgEntities.h"
#include <daECS/core/entityManager.h>
#include <daECS/core/entitySystem.h>
#include <daECS/core/componentTypes.h>
#include <daECS/core/coreEvents.h>
#include <math/dag_TMatrix.h>
#include <daEditorE/editorCommon/entityEditor.h>

// Shared daNetGame integration: every project's F2 gizmos and transform property
// edits use the same native transform component and transactional CSG publisher.
ECS_TAG(render)
ECS_TRACK(transform)
ECS_REQUIRE(ecs::Tag csg_source)
static void csg_editor_transform_es(const ecs::Event &,ecs::EntityId eid,const TMatrix &transform,bool csg__published)
{
  if(csg__published)
    queue_csg_source_transform_update(eid,transform);
}

ECS_TAG(dev,render)
ECS_REQUIRE(ecs::Tag csg_source)
static void csg_editor_save_transform_es(const EditorComponentSavedEvent &event,ecs::EntityId eid,
  const TMatrix &transform,bool csg__published)
{
  if(csg__published && eastl::get<0>(event)==ECS_HASH("transform").hash)
    queue_csg_source_transform_update(eid,transform,true);
}
