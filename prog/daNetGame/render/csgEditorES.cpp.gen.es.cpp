// Built with ECS codegen version 1.0
#include <daECS/core/entitySystem.h>
#include <daECS/core/componentTypes.h>
#include "csgEditorES.cpp.inl"
ECS_DEF_PULL_VAR(csgEditor);
#include <daECS/core/internal/performQuery.h>
static constexpr ecs::ComponentDesc csg_editor_transform_es_comps[] =
{
//start of 3 ro components at [0]
  {ECS_HASH("eid"), ecs::ComponentTypeInfo<ecs::EntityId>()},
  {ECS_HASH("transform"), ecs::ComponentTypeInfo<TMatrix>()},
  {ECS_HASH("csg__published"), ecs::ComponentTypeInfo<bool>()},
//start of 1 rq components at [3]
  {ECS_HASH("csg_source"), ecs::ComponentTypeInfo<ecs::Tag>()}
};
static void csg_editor_transform_es_all_events(const ecs::Event &__restrict evt, const ecs::QueryView &__restrict components)
{
  auto comp = components.begin(), compE = components.end(); G_ASSERT(comp!=compE); do
    csg_editor_transform_es(evt
        , ECS_RO_COMP(csg_editor_transform_es_comps, "eid", ecs::EntityId)
    , ECS_RO_COMP(csg_editor_transform_es_comps, "transform", TMatrix)
    , ECS_RO_COMP(csg_editor_transform_es_comps, "csg__published", bool)
    );
  while (++comp != compE);
}
static ecs::EntitySystemDesc csg_editor_transform_es_es_desc
(
  "csg_editor_transform_es",
  "C:/Users/cisco/develop/DagorEngine/prog/daNetGame/render/csgEditorES.cpp.inl",
  ecs::EntitySystemOps(nullptr, csg_editor_transform_es_all_events),
  empty_span(),
  make_span(csg_editor_transform_es_comps+0, 3)/*ro*/,
  make_span(csg_editor_transform_es_comps+3, 1)/*rq*/,
  empty_span(),
  ecs::EventSetBuilder<>::build(),
  0
,"render","transform");
static constexpr ecs::ComponentDesc csg_editor_save_transform_es_comps[] =
{
//start of 3 ro components at [0]
  {ECS_HASH("eid"), ecs::ComponentTypeInfo<ecs::EntityId>()},
  {ECS_HASH("transform"), ecs::ComponentTypeInfo<TMatrix>()},
  {ECS_HASH("csg__published"), ecs::ComponentTypeInfo<bool>()},
//start of 1 rq components at [3]
  {ECS_HASH("csg_source"), ecs::ComponentTypeInfo<ecs::Tag>()}
};
static void csg_editor_save_transform_es_all_events(const ecs::Event &__restrict evt, const ecs::QueryView &__restrict components)
{
  G_FAST_ASSERT(evt.is<EditorComponentSavedEvent>());
  auto comp = components.begin(), compE = components.end(); G_ASSERT(comp!=compE); do
    csg_editor_save_transform_es(static_cast<const EditorComponentSavedEvent&>(evt)
        , ECS_RO_COMP(csg_editor_save_transform_es_comps, "eid", ecs::EntityId)
    , ECS_RO_COMP(csg_editor_save_transform_es_comps, "transform", TMatrix)
    , ECS_RO_COMP(csg_editor_save_transform_es_comps, "csg__published", bool)
    );
  while (++comp != compE);
}
static ecs::EntitySystemDesc csg_editor_save_transform_es_es_desc
(
  "csg_editor_save_transform_es",
  "C:/Users/cisco/develop/DagorEngine/prog/daNetGame/render/csgEditorES.cpp.inl",
  ecs::EntitySystemOps(nullptr, csg_editor_save_transform_es_all_events),
  empty_span(),
  make_span(csg_editor_save_transform_es_comps+0, 3)/*ro*/,
  make_span(csg_editor_save_transform_es_comps+3, 1)/*rq*/,
  empty_span(),
  ecs::EventSetBuilder<EditorComponentSavedEvent>::build(),
  0
,"dev,render");
