// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <generic/dag_tab.h>
#include <daECS/core/entityId.h>
class DataBlock;
class TMatrix;
namespace ecs { class EntityManager; }
void register_csg_templates(ecs::EntityManager &manager);
bool create_csg_source_entities(const DataBlock &,ecs::EntityId level,Tab<ecs::EntityId> &created);
bool create_csg_runtime_scene(const DataBlock &,ecs::EntityId root,dag::ConstSpan<ecs::EntityId> sources);
void destroy_csg_runtime_scene(ecs::EntityId root);
void queue_csg_source_transform_update(ecs::EntityId source,const TMatrix &world,bool save_to_scene=false);
