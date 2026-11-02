// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <csg/scene.h>
#include <csg/runtime.h>
#include <3d/dag_materialData.h>
#include <shaders/dag_shaderMesh.h>
#include <math/dag_mesh.h>
#include <math/dag_frustum.h>
#include <drv/3d/dag_driver.h>
#include <drv/3d/dag_matricesAndPerspective.h>
#include <gameRes/collisionResourceBuilder.h>
#include <gamePhys/collision/collisionLib.h>
#include <unwrapMapping/autoUnwrap.h>
#include <osApiWrappers/dag_miscApi.h>
#include <startup/dag_globalSettings.h>
#include <ioSys/dag_dataBlock.h>
#include <algorithm>
#include <map>
#include <cmath>
#include <chrono>
#include <debug/dag_debug.h>
#include <memory/dag_dbgMem.h>
#include <render/lruCollision.h>
#include <atomic>

namespace csg
{
namespace
{
std::vector<Scene *> scenes;
Point3 point(Vec p) { return {float(p.x),float(p.y),float(p.z)}; }
struct CollisionDeleter
{
  void operator()(dacoll::RuntimeStaticCollision *p) const { dacoll::destroy_runtime_static_collision(p); }
};
struct Chunk
{
  eastl::shared_ptr<LRURendinstCollision> giCache;
  rendinst::riex_handle_t giHandle = rendinst::RIEX_HANDLE_NULL;
  BBox3 bounds;
  std::vector<std::unique_ptr<ShaderMesh>> render;
  // Keep generated UV1 data with its immutable geometry/collision revision,
  // even when the active material does not consume lightmaps in its shader.
  std::vector<Point2> lightmapVertices;
  std::vector<TFace> lightmapFaces;
  std::vector<unsigned short> lightmapPages;
  std::unique_ptr<dacoll::RuntimeStaticCollision,CollisionDeleter> collision;
  ~Chunk() { if (giCache && giHandle != rendinst::RIEX_HANDLE_NULL) giCache->releaseWorldCollision(giHandle); }
};
}
struct Scene::Impl
{
  SceneSettings settings;
  std::map<std::string,Ptr<MaterialData>> materials;
  std::map<uint64_t,std::shared_ptr<Chunk>> chunks;
  RuntimeModel model;
  BBox3 changedBounds;
  std::atomic<uint64_t> renderedRevision{0};

  std::shared_ptr<Chunk> prepare(const csg::Mesh &source,Diagnostics &errors)
  {
    auto start=std::chrono::steady_clock::now();
    auto elapsed=[&] { return std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count(); };
    auto fail=[&](const char *message)->std::shared_ptr<Chunk> {
      errors.push_back({Code::InvalidResult,0,0,message}); return {};
    };
    auto prepared=std::make_shared<Chunk>();
    if(source.faces.empty()) return prepared;
    csg::Mesh canonical; Vec origin;
    if(!prepareFloatPublication(source,canonical,origin,errors)) return {};
    double floatMs=elapsed();
    ::Mesh mesh; std::vector<MaterialData *> materialList;
    std::map<std::string,int> materialIds;
    for(auto p:canonical.vertices) { mesh.vert.push_back(point(p)); prepared->bounds+=point(p); }
    for(const auto &face:canonical.faces) {
      auto material=materials.find(face.surface.material);
      if(material==materials.end() || !material->second) {
        errors.push_back({Code::InvalidResult,face.sourceBrush,face.id,
          "Runtime CSG material '"+face.surface.material+"' is not in the exported palette"}); return {};
      }
      auto inserted=materialIds.emplace(face.surface.material,int(materialIds.size()));
      if(inserted.second) materialList.push_back(material->second);
      ::Face triangle{}; triangle.mat=inserted.first->second; triangle.smgr=face.surface.smoothing;
      TFace uv{};
      for(int j=0;j<3;++j) {
        triangle.v[j]=face.vertices[j]; uv.t[j]=mesh.tvert[0].size();
        auto tc=textureCoordinates(face.surface,canonical.vertices[face.vertices[j]]);
        mesh.tvert[0].push_back({float(tc[0]),float(tc[1])});
      }
      mesh.face.push_back(triangle); mesh.tface[0].push_back(uv);
    }
    double conversionMs=elapsed();
    struct MappingScope
    {
      MappingScope(int size) { AutoUnwrapMapping::start_mapping_in_memory(size); }
      ~MappingScope() { AutoUnwrapMapping::finish_mapping(); }
    } mapping(settings.lightmapSize);
    QuietProgressIndicator progress; SimpleProgressCB cancel;
    int handle=AutoUnwrapMapping::request_mapping(mesh.face.data(),mesh.face.size(),mesh.vert.data(),mesh.vert.size(),
      settings.lightmapSampleSize,false,AutoUnwrapMapping::SCHEME_DAGOR);
    double requestMs=elapsed();
    AutoUnwrapMapping::prepare_facegroups(progress,cancel);
    double chartsMs=elapsed();
    int atlasCount=AutoUnwrapMapping::repack_facegroups(1,nullptr,0,progress,cancel);
    double packingMs=elapsed();
    if(handle<0 || atlasCount<=0 || cancel.mustStop) return fail("Runtime CSG lightmap mapping failed");
    std::vector<unsigned short> pages(mesh.face.size()); mesh.tface[1].resize(mesh.face.size());
    Point2 *uv=nullptr; int count=0;
    AutoUnwrapMapping::get_final_mapping(handle,pages.data(),sizeof(unsigned short),mesh.tface[1].data(),uv,count);
    if(!uv || count<=0) return fail("Runtime CSG lightmap coordinates are empty");
    mesh.tvert[1].resize(count); for(int i=0;i<count;++i) mesh.tvert[1][i]=uv[i];
    mesh.calc_ngr(); mesh.calc_vertnorms();
    for(auto &normal:mesh.vertnorm) normal=-normal;
    double mappingMs=elapsed();
    if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeBenchmark",false))
      debug("CSG runtime UV preparation: float %.3f conversion %.3f request %.3f charts %.3f packing %.3f normals %.3f ms",floatMs,
        conversionMs-floatMs,requestMs-conversionMs,chartsMs-requestMs,packingMs-chartsMs,mappingMs-packingMs);
    // createSimple uses 16-bit indices. Bound batches by triangle count, even
    // for fully split hard normals and UV seams (at most 60,000 vertices).
    for(size_t mat=0;mat<materialList.size();++mat) {
      Ptr<ShaderMaterial> shader=new_shader_material(*materialList[mat]);
      if(!shader) return fail("Runtime CSG shader material could not be created");
      std::map<std::pair<unsigned,int>,std::vector<int>> batches;
      std::map<unsigned,int> pageCounts;
      for(int i=0;i<mesh.face.size();++i) if(mesh.face[i].mat==mat)
        batches[{pages[i],pageCounts[pages[i]]++/20000}].push_back(i);
      for(const auto &batch:batches) {
        ::Mesh subset(mesh); std::vector<bool> keep(mesh.face.size());
        for(auto i:batch.second) keep[i]=true;
        for(int i=mesh.face.size()-1;i>=0;--i) if(!keep[i]) subset.removeFacesFast(i,1);
        auto *render=ShaderMesh::createSimple(subset,shader,"Runtime CSG");
        if(!render) return fail("Runtime CSG GPU mesh creation failed");
        prepared->render.emplace_back(render);
        std::vector<TEXTUREID> textures;
        for(const auto &element:render->getAllElems()) if(element.e)
          for(int i=0;i<element.e->getTextureCount();++i) {
            auto texture=element.e->getTexture(i); if(texture==BAD_TEXTUREID) continue;
            textures.push_back(texture);
          }
        if(!prefetch_and_wait_managed_textures_loaded({textures.data(),textures.size()},false))
          return fail("Runtime CSG material textures could not be loaded");
      }
    }
    double renderMs=elapsed();
    CollisionResourceBuilder collision;
    dag::Vector<Point3_vec4> vertices; dag::Vector<uint32_t> indices;
    for(const auto &p:mesh.vert) vertices.push_back(Point3_vec4(p));
    for(const auto &f:mesh.face) for(auto index:f.v) indices.push_back(index);
    collision.addMeshNode("csg",PHYSMAT_DEFAULT,TMatrix::IDENT,prepared->bounds,vertices,indices);
    collision.collapse("Runtime CSG");
    collision.recomputeBounds();
    Ptr<CollisionResource> resource=collision.build("Runtime CSG");
    if(!resource || resource->getAllNodes().empty() || resource->boundingBox.isempty())
      return fail("Runtime CSG collision resource creation failed");
    prepared->collision.reset(dacoll::prepare_runtime_static_collision(resource));
    if(!prepared->collision) return fail("Runtime CSG physics cooking failed");
    prepared->giCache=LRURendinstCollision::acquire();
    prepared->giHandle=prepared->giCache->prepareWorldCollision(resource);
    if(prepared->giHandle==rendinst::RIEX_HANDLE_NULL) return fail("Runtime CSG GI collision preparation failed");
    prepared->lightmapVertices.assign(mesh.tvert[1].begin(),mesh.tvert[1].end());
    prepared->lightmapFaces.assign(mesh.tface[1].begin(),mesh.tface[1].end());
    prepared->lightmapPages=std::move(pages);
    if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeBenchmark",false))
      debug("CSG runtime prepare faces=%d: mapping %.3f render %.3f collision %.3f ms",mesh.face.size(),mappingMs,renderMs-mappingMs,elapsed()-renderMs);
    return prepared;
  }
};

Scene::Scene(const SceneSettings &settings,const std::vector<SceneMaterial> &materials):impl(new Impl)
{
  impl->settings=settings;
  for(const auto &entry:materials) impl->materials[entry.name]=entry.data;
  scenes.push_back(this);
}
Scene::~Scene() { scenes.erase(std::find(scenes.begin(),scenes.end(),this)); }
const Document &Scene::document() const { return impl->model.document(); }
const Result &Scene::result() const { return impl->model.result(); }
uint64_t Scene::lastRenderedRevision() const { return impl->renderedRevision.load(std::memory_order_relaxed); }
const BBox3 &Scene::lastChangedBounds() const { return impl->changedBounds; }
bool Scene::update(Document candidate,Diagnostics &errors)
{
  DagDbgMem::ForcedProfileCallStackRAII allocationProfile;
  auto start=std::chrono::steady_clock::now();
  if(!is_main_thread()) {
    errors.push_back({Code::InvalidDocument,0,0,"Runtime CSG scene updates require the main thread"}); return false;
  }
  const auto &settings=impl->settings;
  if(settings.lightmapSize<32 || settings.lightmapSize>2048 || (settings.lightmapSize&(settings.lightmapSize-1)) ||
    !std::isfinite(settings.lightmapSampleSize) || settings.lightmapSampleSize<=0) {
    errors.push_back({Code::InvalidResult,0,0,"Invalid runtime CSG lightmap settings"}); return false;
  }
  return impl->model.commit(std::move(candidate),[&](const Result &result) {
    double evaluationMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count();
    auto inputs=result.chunks;
    if(inputs.empty() && result.mesh && !result.mesh->faces.empty()) {
      Node key; key.brush=*result.mesh; inputs.push_back({fingerprint(key),result.mesh});
    }
    std::map<uint64_t,std::shared_ptr<Chunk>> next;
    for(const auto &input:inputs) {
      auto old=impl->chunks.find(input.hash);
      auto chunk=old!=impl->chunks.end() ? old->second:impl->prepare(*input.mesh,errors);
      if(!chunk) return false;
      next.emplace(input.hash,std::move(chunk));
    }
    std::vector<dacoll::RuntimeStaticCollision *> removed,added;
    BBox3 changedBounds;
    for(const auto &[hash,chunk]:impl->chunks) if(!next.count(hash)) changedBounds+=chunk->bounds;
    for(const auto &[hash,chunk]:next) if(!impl->chunks.count(hash)) changedBounds+=chunk->bounds;
    for(const auto &[hash,chunk]:impl->chunks) if(!next.count(hash) && chunk->collision) removed.push_back(chunk->collision.get());
    for(const auto &[hash,chunk]:next) if(!impl->chunks.count(hash) && chunk->collision) added.push_back(chunk->collision.get());
    if((!removed.empty() || !added.empty()) &&
      !dacoll::replace_runtime_static_collisions({removed.data(),removed.size()},{added.data(),added.size()})) return false;
    // No allocating/fallible operation remains after collision publication.
    for(const auto &[hash,chunk]:next) if(!impl->chunks.count(hash))
      LRURendinstCollision::publishWorldCollision(chunk->giHandle);
    impl->chunks.swap(next); impl->changedBounds=changedBounds;
    if(dgs_get_settings()->getBlockByNameEx("debug")->getBool("csgRuntimeBenchmark",false))
      debug("CSG runtime scene: evaluation %.3f publication %.3f ms",evaluationMs,
        std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()-evaluationMs);
    return true;
  },errors);
}
void renderScenes(const Frustum &frustum,bool main_view)
{
  if(scenes.empty()) return;
  TMatrix previous; d3d::gettm(TM_WORLD,previous);
  d3d::settm(TM_WORLD,TMatrix::IDENT);
  for(const auto *scene:scenes) {
    for(const auto &[hash,chunk]:scene->impl->chunks) {
    if(!chunk->render.empty() && frustum.testBoxB(chunk->bounds))
      for(const auto &mesh:chunk->render) {
        // Match the normal dynamic-mesh renderer's streaming demand. A bound
        // normal map must stay resident after the initial publication check.
        for(const auto &element:mesh->getAllElems()) if(element.e) element.e->setReqTexLevel();
        mesh->render();
      }
    }
    if(main_view) scene->impl->renderedRevision.store(scene->result().revision,std::memory_order_relaxed);
  }
  d3d::settm(TM_WORLD,previous);
}
}
