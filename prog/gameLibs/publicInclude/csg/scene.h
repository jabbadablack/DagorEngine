// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <csg/geometry.h>
class MaterialData;
class Frustum;
class BBox3;
namespace csg
{
struct SceneSettings
{
  int lightmapSize = 1024;
  float lightmapSampleSize = 0.1f;
};
struct SceneMaterial
{
  std::string name; // Source surface material name; empty means the default.
  MaterialData *data = nullptr;
};
// Owner-thread, engine-published CSG. A successful update replaces rendering,
// material/lightmap UVs and world collision as one revision. Failures keep all
// previously accepted resources. Destroy before the renderer/physics world.
class Scene
{
public:
  Scene(const SceneSettings &settings, const std::vector<SceneMaterial> &materials);
  ~Scene();
  Scene(const Scene &) = delete;
  Scene &operator=(const Scene &) = delete;
  bool update(Document candidate, Diagnostics &errors);
  const Document &document() const;
  const Result &result() const;
  uint64_t lastRenderedRevision() const;
  const BBox3 &lastChangedBounds() const;
private:
  struct Impl;
  std::unique_ptr<Impl> impl;
  friend void renderScenes(const Frustum &frustum,bool main_view);
};
// Called by the engine's existing static-scene rendering pass, including shadows.
void renderScenes(const Frustum &frustum,bool main_view=false);
}
