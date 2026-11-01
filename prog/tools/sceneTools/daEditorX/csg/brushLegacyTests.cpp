// Copyright (C) Gaijin Games KFT. All rights reserved.
#include "../services/csgEntMgr/csgApi.h"
#include <libTools/CSG/brush.h>
#include <memory>
#include <stdexcept>
#include <cmath>

namespace
{
void require(bool value,const char *message) { if(!value) throw std::runtime_error(message); }
Mesh inputMesh(const csg::Mesh &source,int material)
{
  csg::Mesh triangles; csg::Diagnostics errors;
  require(csg::triangulateForPublication(source,triangles,errors),"Legacy fixture triangulation failed");
  Mesh mesh;
  for(auto p:triangles.vertices)
  {
    mesh.vert.push_back(Point3(p.x,p.y,p.z));
    mesh.tvert[0].push_back(Point2(2*p.x+3*p.y+4*p.z+0.25,-p.x+2*p.y+3*p.z+0.5));
  }
  for(const auto &f:triangles.faces)
  {
    Face face{}; TFace uv{};
    for(int i=0;i<3;++i) face.v[i]=uv.t[i]=f.vertices[i];
    face.mat=material; face.smgr=material ? 9:5;
    mesh.face.push_back(face); mesh.tface[0].push_back(uv);
  }
  return mesh;
}
struct DeletePoly { BasicCSG *backend; void operator()(void *p) const { if(p) backend->delete_poly(p); } };
void cutFixture(const csg::Mesh &cutter,double expectedVolume)
{
  std::unique_ptr<BasicCSG> backend(make_new_csg(1));
  auto outer=inputMesh(csg::box({4,4,4}),0),inner=inputMesh(cutter,1);
  using Poly=std::unique_ptr<void,DeletePoly>;
  Poly a(backend->create_poly(nullptr,outer,0,true),{backend.get()});
  Poly b(backend->create_poly(nullptr,inner,1,true),{backend.get()});
  require(a && b,"Legacy closed-mesh entry point rejected fixture");
  Poly result(backend->op(BasicCSG::A_MINUS_B,a.get(),nullptr,b.get(),nullptr),{backend.get()});
  require(bool(result),"Legacy building/prefab cut failed");
  Mesh output; backend->convert(result.get(),output);
  csg::Mesh solid;
  for(auto p:output.vert) solid.vertices.push_back({p.x,p.y,p.z});
  bool cutterMaterial=false;
  require(output.tface[0].size()==output.face.size(),"Legacy UV faces lost");
  for(int fi=0;fi<output.face.size();++fi)
  {
    const auto &face=output.face[fi]; csg::Face f;
    for(int corner=0;corner<3;++corner)
    {
      f.vertices.push_back(face.v[corner]); auto p=output.vert[face.v[corner]];
      auto uv=output.tvert[0][output.tface[0][fi].t[corner]];
      require(std::abs(uv.x-(2*p.x+3*p.y+4*p.z+0.25))<1e-4 &&
        std::abs(uv.y-(-p.x+2*p.y+3*p.z+0.5))<1e-4,"Legacy interpolated UV changed");
    }
    solid.faces.push_back(f);
    require(face.mat<=1 && face.smgr==(face.mat ? 9u:5u),"Legacy material/smoothing changed");
    cutterMaterial|=face.mat==1;
  }
  csg::Diagnostics errors;
  require(csg::validate(solid,errors),"Legacy fixture topology changed");
  require(std::abs(csg::volume(solid)-expectedVolume)<1e-6,"Legacy fixture volume changed");
  require(cutterMaterial,"Legacy cutter surface attribution lost");
}
}
void runLegacyCSGAcceptance()
{
  cutFixture(csg::box({2,2,2}),56);
  csg::Mesh l;
  for(double z:{-1.0,1.0}) for(csg::Vec p:std::vector<csg::Vec>{{-1,-1,0},{1,-1,0},{1,0,0},{0,0,0},{0,1,0},{-1,1,0}})
    l.vertices.push_back({p.x,p.y,z});
  csg::Face bottom,top; bottom.vertices={5,4,3,2,1,0}; top.vertices={6,7,8,9,10,11}; l.faces={bottom,top};
  for(uint32_t i=0;i<6;++i) { csg::Face f; auto next=(i+1)%6; f.vertices={i,next,next+6,i+6}; l.faces.push_back(f); }
  cutFixture(l,58);
}
