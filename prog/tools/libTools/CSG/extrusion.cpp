// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include "precise.h"
#include <carve/triangle_intersection.hpp>
#include <algorithm>
#include <cmath>
#include <numeric>

namespace csg
{
namespace
{
constexpr double pi=3.14159265358979323846;
Vec rotate(Vec p,Vec axis,double angle)
{ return p*std::cos(angle)+cross(axis,p)*std::sin(angle)+axis*(dot(axis,p)*(1-std::cos(angle))); }
double orient(Vec a,Vec b,Vec c) { return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x); }
// Reject crossings between non-neighboring surface triangles. Shared edges and
// vertices are legitimate; sharing one vertex does not exempt the whole pair.
bool crosses(const Mesh &m,const Face &a,const Face &b,double eps,bool componentContact)
{
  Vec p[3],q[3]; unsigned shared=0;
  for(int i=0;i<3;++i) { p[i]=m.vertices[a.vertices[i]]; q[i]=m.vertices[b.vertices[i]]; }
  for(int i=0;i<3;++i) for(int j=0;j<3;++j) if(a.vertices[i]==b.vertices[j]) ++shared;
  auto n=normalized(cross(p[1]-p[0],p[2]-p[0]));
  auto k=normalized(cross(q[1]-q[0],q[2]-q[0]));
  bool coplanar=length(cross(n,k))<1e-10 && std::abs(dot(n,q[0]-p[0]))<eps;
  if(coplanar)
  {
    auto u=normalized(p[1]-p[0]),v=cross(n,u);
    auto project=[&](Vec x) { return Vec{dot(x-p[0],u),dot(x-p[0],v),0}; };
    Vec x[3],y[3]; for(int i=0;i<3;++i) { x[i]=project(p[i]); y[i]=project(q[i]); }
    if(orient(x[0],x[1],x[2])<0) std::swap(x[1],x[2]);
    if(orient(y[0],y[1],y[2])<0) std::swap(y[1],y[2]);
    carve::geom::vector<2> left[3],right[3];
    for(int i=0;i<3;++i) { left[i]=carve::geom::VECTOR(x[i].x,x[i].y); right[i]=carve::geom::VECTOR(y[i].x,y[i].y); }
    auto intersection=carve::geom::triangle_intersection_exact(left,right);
    return intersection==carve::geom::TR_TYPE_INT || (intersection==carve::geom::TR_TYPE_TOUCH && !shared && !componentContact);
  }
  carve::geom::vector<3> left[3],right[3];
  for(int i=0;i<3;++i) {
    left[i]=carve::geom::VECTOR(p[i].x,p[i].y,p[i].z);
    right[i]=carve::geom::VECTOR(q[i].x,q[i].y,q[i].z);
  }
  auto intersection=carve::geom::triangle_intersection_exact(left,right);
  return intersection==carve::geom::TR_TYPE_INT || (intersection==carve::geom::TR_TYPE_TOUCH && !shared && !componentContact);
}
bool noCrossings(const Mesh &m,Diagnostics &errors)
{
  struct Bounds { Vec lo,hi; size_t face; };
  std::vector<Bounds> bounds;
  std::vector<uint32_t> parent(m.vertices.size()); std::iota(parent.begin(),parent.end(),0);
  auto root=[&](uint32_t i) { while(parent[i]!=i) { parent[i]=parent[parent[i]]; i=parent[i]; } return i; };
  for(const auto &face:m.faces) for(auto v:face.vertices) parent[root(v)]=root(face.vertices[0]);
  double extent=0;
  for(size_t i=0;i<m.faces.size();++i)
  {
    Bounds b{m.vertices[m.faces[i].vertices[0]],m.vertices[m.faces[i].vertices[0]],i};
    for(auto j:m.faces[i].vertices) {
      auto p=m.vertices[j]; b.lo={std::min(b.lo.x,p.x),std::min(b.lo.y,p.y),std::min(b.lo.z,p.z)};
      b.hi={std::max(b.hi.x,p.x),std::max(b.hi.y,p.y),std::max(b.hi.z,p.z)};
      extent=std::max(extent,length(p-m.vertices[0]));
    } bounds.push_back(b);
  }
  std::sort(bounds.begin(),bounds.end(),[](const Bounds &a,const Bounds &b){return a.lo.x<b.lo.x;});
  double eps=std::max(1e-10,extent*1e-10); size_t candidates=0;
  for(size_t i=0;i<bounds.size();++i) for(size_t j=i+1;j<bounds.size() && bounds[j].lo.x<=bounds[i].hi.x+eps;++j)
  {
    const auto &a=bounds[i],&b=bounds[j];
    if(a.lo.y>b.hi.y+eps || b.lo.y>a.hi.y+eps || a.lo.z>b.hi.z+eps || b.lo.z>a.hi.z+eps) continue;
    if(++candidates>2000000) { errors.push_back({Code::InvalidMesh,0,0,"Sweep intersection-validation budget exceeded; reduce subdivisions"}); return false; }
    if(crosses(m,m.faces[a.face],m.faces[b.face],eps,root(m.faces[a.face].vertices[0])!=root(m.faces[b.face].vertices[0]))) {
      errors.push_back({Code::InvalidMesh,0,m.faces[a.face].id,"Extrusion folds or intersects itself"}); return false;
    }
  }
  return true;
}
}
bool validateClosedMesh(const Mesh &mesh,Diagnostics &errors)
{
  if(!validate(mesh,errors)) return false;
  Mesh triangles; if(!triangulateForPublication(mesh,triangles,errors)) return false;
  return noCrossings(triangles,errors);
}
bool generateExtrusion(const Extrusion &s,Mesh &output,Diagnostics &errors)
{
  auto fail=[&](const char *message) { errors.push_back({Code::InvalidMesh,0,0,message}); return false; };
  if(s.polygon.size()<3 || s.polygon.size()>256) return fail("Extrusion profile requires 3 to 256 points");
  if(!s.surfaces.empty() && s.surfaces.size()!=s.polygon.size()+2) return fail("Extrusion surface settings do not match the profile");
  for(auto p:s.polygon) if(!finite(p) || p.z!=0) return fail("Extrusion profile must contain finite XY points");
  std::vector<Mesh> triangles;
  if(!extrudeOutline(s.polygon,{0,0,1},triangles,errors)) return false;
  std::vector<std::array<uint32_t,3>> caps;
  for(const auto &prism:triangles)
  {
    std::array<uint32_t,3> triangle{};
    for(unsigned i=0;i<3;++i) {
      auto p=prism.vertices[i]; auto it=std::find_if(s.polygon.begin(),s.polygon.end(),[&](Vec q){return p.x==q.x && p.y==q.y;});
      triangle[i]=uint32_t(it-s.polygon.begin());
    }
    caps.push_back(triangle);
  }
  std::vector<std::vector<Vec>> rings; bool joined=false;
  if(s.mode==ExtrusionMode::Depth)
  {
    if(!std::isfinite(s.depth) || s.depth<=1e-8) return fail("Extrusion depth must be positive and finite");
    rings={s.polygon,s.polygon}; for(auto &p:rings[1]) p.z=-s.depth;
  }
  else if(s.mode==ExtrusionMode::Spin)
  {
    if(!std::isfinite(s.spinDegrees) || s.spinDegrees<=0 || s.spinDegrees>360 || s.spinSides<3 || s.spinSides>512)
      return fail("Spin requires 0 < degrees <= 360 and 3 to 512 sides");
    for(auto p:s.polygon) if(p.x<0) return fail("Spin profile cannot cross the rotation axis");
    joined=s.spinDegrees==360;
    for(unsigned i=0;i<s.spinSides+unsigned(!joined);++i) {
      double degrees=s.spinDegrees*double(i)/s.spinSides,angle=degrees*pi/180;
      double cosine=std::cos(angle),sine=std::sin(angle);
      // Cardinal samples are exact by construction. Keep their exact planes
      // instead of creating sub-float slivers from sin(pi)'s rounding residue.
      if(degrees==std::round(degrees/90)*90) {
        unsigned quadrant=unsigned(std::llround(degrees/90))%4;
        cosine=quadrant==0 ? 1:quadrant==2 ? -1:0;
        sine=quadrant==1 ? 1:quadrant==3 ? -1:0;
      }
      std::vector<Vec> ring;
      for(auto p:s.polygon) ring.push_back({p.x*cosine,p.y,-p.x*sine});
      rings.push_back(std::move(ring));
    }
  }
  else if(s.mode==ExtrusionMode::Path)
  {
    if(s.path.size()<2 || s.path.size()>128 || s.pathSubdivisions<1 || s.pathSubdivisions>128 || (s.pathJoined && s.path.size()<3))
      return fail("Path requires 2 to 128 control points and 1 to 128 subdivisions (closed paths require 3 points)");
    for(const auto &p:s.path) if(!finite(p.position)||!finite(p.incoming)||!finite(p.outgoing)||!std::isfinite(p.tilt))
      return fail("Non-finite Bezier control point");
    joined=s.pathJoined;
    struct Sample { Vec p,t; double tilt; }; std::vector<Sample> samples;
    unsigned segments=unsigned(s.path.size())-unsigned(!joined);
    for(unsigned i=0;i<segments;++i) {
      const auto &a=s.path[i],&b=s.path[(i+1)%s.path.size()];
      if(length(a.position-b.position)<1e-8) return fail("Repeated path control positions");
      for(unsigned j=0;j<s.pathSubdivisions+unsigned(!joined && i+1==segments);++j) {
        double t=double(j)/s.pathSubdivisions,u=1-t;
        Vec p0=a.position,p1=p0+a.outgoing,p3=b.position,p2=p3+b.incoming;
        Vec p=p0*(u*u*u)+p1*(3*u*u*t)+p2*(3*u*t*t)+p3*(t*t*t);
        Vec tangent=(p1-p0)*(3*u*u)+(p2-p1)*(6*u*t)+(p3-p2)*(3*t*t);
        if(length(tangent)<1e-10) {
          if(j==0) tangent=length(p2-p0)>1e-10 ? p2-p0:p3-p0;
          else if(j==s.pathSubdivisions) tangent=length(p3-p1)>1e-10 ? p3-p1:p3-p0;
          else return fail("Bezier path has an interior cusp");
        }
        if(!samples.empty() && length(p-samples.back().p)<1e-8) return fail("Path has collapsed sample intervals");
        samples.push_back({p,normalized(tangent),a.tilt*u+b.tilt*t});
      }
    }
    Vec up={0,1,0},side=normalized(cross(samples[0].t,up));
    if(length(side)<0.5) side=normalized(cross(samples[0].t,Vec{1,0,0}));
    Vec previous=samples[0].t;
    std::vector<Vec> sides;
    for(const auto &sample:samples) {
      Vec axis=cross(previous,sample.t); double sine=length(axis),cosine=std::clamp(dot(previous,sample.t),-1.0,1.0);
      if(cosine<-0.999999) return fail("Path reverses direction; add a bend with nonzero radius");
      if(sine>1e-12) side=rotate(side,axis/sine,std::atan2(sine,cosine));
      side=normalized(side-sample.t*dot(side,sample.t)); sides.push_back(side); previous=sample.t;
    }
    // Distribute parallel-transport seam twist across closed curves.
    double correction=0;
    if(joined) {
      Vec axis=cross(previous,samples[0].t); double sine=length(axis);
      Vec end=sides.back(); if(sine>1e-12) end=rotate(end,axis/sine,std::atan2(sine,dot(previous,samples[0].t)));
      correction=std::atan2(dot(samples[0].t,cross(end,sides[0])),dot(end,sides[0]));
    }
    for(size_t i=0;i<samples.size();++i) {
      const auto &sample=samples[i]; Vec x=rotate(sides[i],sample.t,sample.tilt+correction*double(i)/samples.size());
      Vec y=cross(x,sample.t); std::vector<Vec> ring;
      for(auto p:s.polygon) ring.push_back(sample.p+x*p.x+y*p.y);
      rings.push_back(std::move(ring));
    }
  }
  else return fail("Unknown extrusion mode");
  if(rings.size()*s.polygon.size()>16384) return fail("Extrusion exceeds the 16384-vertex validation budget");
  Mesh result; std::vector<std::vector<uint32_t>> indices;
  // Only the revolution axis is intentionally shared between rings. Do not
  // weld arbitrary close vertices: that conceals folded/self-touching sweeps.
  std::vector<uint32_t> axis(s.polygon.size(),UINT32_MAX);
  for(const auto &ring:rings) {
    std::vector<uint32_t> ids;
    for(size_t i=0;i<ring.size();++i) {
      if(s.mode==ExtrusionMode::Spin && s.polygon[i].x==0 && axis[i]!=UINT32_MAX) ids.push_back(axis[i]);
      else { uint32_t id=uint32_t(result.vertices.size()); result.vertices.push_back(ring[i]); ids.push_back(id);
        if(s.mode==ExtrusionMode::Spin && s.polygon[i].x==0) axis[i]=id; }
    } indices.push_back(std::move(ids));
  }
  auto face=[&](uint32_t a,uint32_t b,uint32_t c,Id surface,Vec uv0,Vec uv1,Vec uv2) {
    if(a==b || b==c || a==c) return;
    Face f; f.vertices={a,b,c}; f.id=surface;
    auto settings=s.surfaces.empty() ? Extrusion::FaceSettings{s.surface,true}:s.surfaces[size_t(surface-1)];
    f.surface=settings.surface;
    if(settings.automaticUv && !f.surface.worldLocked) {
      mapSurfaceTriangle(f.surface,result.vertices[a],result.vertices[b],result.vertices[c],uv0,uv1,uv2);
    }
    result.faces.push_back(std::move(f));
  };
  if(!joined) for(auto t:caps) {
    face(indices.front()[t[2]],indices.front()[t[1]],indices.front()[t[0]],1,s.polygon[t[2]],s.polygon[t[1]],s.polygon[t[0]]);
    face(indices.back()[t[0]],indices.back()[t[1]],indices.back()[t[2]],2,s.polygon[t[0]],s.polygon[t[1]],s.polygon[t[2]]);
  }
  std::vector<double> perimeter(s.polygon.size()+1),travel(rings.size()+unsigned(joined));
  for(size_t i=0;i<s.polygon.size();++i) perimeter[i+1]=perimeter[i]+length(s.polygon[(i+1)%s.polygon.size()]-s.polygon[i]);
  for(size_t i=1;i<travel.size();++i) {
    Vec before{},after{};
    for(auto p:rings[i-1]) before=before+p;
    for(auto p:rings[i%rings.size()]) after=after+p;
    travel[i]=travel[i-1]+length(after-before)/s.polygon.size();
  }
  for(size_t i=0;i<rings.size()-unsigned(!joined);++i) for(size_t j=0;j<s.polygon.size();++j) {
    size_t next=(i+1)%rings.size(),edge=(j+1)%s.polygon.size();
    auto uv=[&](size_t ring,size_t vertex,double around) {
      double along=s.mode==ExtrusionMode::Spin ? double(ring)*s.spinDegrees*pi/180/s.spinSides*s.polygon[vertex].x:travel[ring];
      return Vec{along,around,0};
    };
    auto a=uv(i,j,perimeter[j]),b=uv(i,edge,perimeter[j+1]),c=uv(i+1,edge,perimeter[j+1]),d=uv(i+1,j,perimeter[j]);
    face(indices[i][j],indices[i][edge],indices[next][edge],j+3,a,b,c);
    face(indices[i][j],indices[next][edge],indices[next][j],j+3,a,c,d);
  }
  if(volume(result)<0) for(auto &f:result.faces) std::reverse(f.vertices.begin(),f.vertices.end());
  if(!validate(result,errors) || !noCrossings(result,errors)) return false;
  output=std::move(result); return true;
}
}
