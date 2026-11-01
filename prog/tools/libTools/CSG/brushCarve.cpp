// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include <carve/csg.hpp>
#include <carve/interpolator.hpp>
#include <carve/csg_triangulator.hpp>
#include <algorithm>
#include <cmath>
#include <functional>
#include <map>
#include <set>
#include <stdexcept>

namespace csg
{
namespace
{
using Poly = carve::mesh::MeshSet<3>;
using Attribute = carve::interpolate::FaceAttr<Face>;
struct Bounds
{
  Vec lo,hi;
  explicit Bounds(const Mesh &m) : lo(m.vertices.front()),hi(lo)
  {
    for (auto p:m.vertices)
    {
      lo={std::min(lo.x,p.x),std::min(lo.y,p.y),std::min(lo.z,p.z)};
      hi={std::max(hi.x,p.x),std::max(hi.y,p.y),std::max(hi.z,p.z)};
    }
  }
};
bool separated(const Bounds &a,const Bounds &b,bool includeContact)
{
  return includeContact ? a.hi.x<=b.lo.x || b.hi.x<=a.lo.x || a.hi.y<=b.lo.y || b.hi.y<=a.lo.y || a.hi.z<=b.lo.z || b.hi.z<=a.lo.z :
    a.hi.x<b.lo.x || b.hi.x<a.lo.x || a.hi.y<b.lo.y || b.hi.y<a.lo.y || a.hi.z<b.lo.z || b.hi.z<a.lo.z;
}
// Preserve separate closed components for contacts of dimension 0 or 1. Face
// contacts must still go through Carve, which removes internal coincident faces.
bool zeroAreaContact(const Bounds &a,const Bounds &b)
{
  // Decimal grid steps can differ by a few ulps after translation. Use the
  // validation-scale tolerance, not exact equality, for zero-area contact.
  double eps=std::max(1e-10,std::max(length(a.hi-a.lo),length(b.hi-b.lo))*1e-10);
  auto contact=[&](double ah,double bl,double bh,double al) {
    return std::abs(ah-bl)<=eps || std::abs(bh-al)<=eps;
  };
  unsigned zero=unsigned(contact(a.hi.x,b.lo.x,b.hi.x,a.lo.x))+unsigned(contact(a.hi.y,b.lo.y,b.hi.y,a.lo.y))+
    unsigned(contact(a.hi.z,b.lo.z,b.hi.z,a.lo.z));
  return zero>=2;
}
std::unique_ptr<Poly> makePoly(const Mesh &m,Vec origin,Attribute &attr,const Surface *overrideSurface)
{
  std::vector<Poly::vertex_t> vertices;
  for (auto p:m.vertices) { p=p-origin; vertices.emplace_back(carve::geom::VECTOR(p.x,p.y,p.z)); }
  std::vector<Poly::face_t *> faces;
  // Poly takes ownership of these faces on success.
  try
  {
    for (const auto &f:m.faces)
    {
      std::vector<Poly::vertex_t *> v;
      for (auto i:f.vertices) v.push_back(&vertices[i]);
      auto *face=new Poly::face_t(v.begin(),v.end()); faces.push_back(face);
      Face source=f; source.vertices.clear();
      if (overrideSurface) source.surface=*overrideSurface;
      attr.setAttribute(face,source);
    }
    return std::unique_ptr<Poly>(new Poly(faces));
  }
  catch (...)
  {
    // MeshSet constructors may have adopted faces already. Do not recover
    // ownership here; prevalidation excludes the ordinary invalid-index cases.
    throw;
  }
}
Mesh concatenate(const Mesh &a,const Mesh &b)
{
  Mesh r=a; uint32_t offset=uint32_t(r.vertices.size());
  r.vertices.insert(r.vertices.end(),b.vertices.begin(),b.vertices.end());
  for (auto f:b.faces) { for (auto &i:f.vertices) i+=offset; r.faces.push_back(std::move(f)); }
  return r;
}
bool componentsSeparate(const Mesh &a,const Bounds &b)
{
  std::vector<uint32_t> parent(a.vertices.size());
  for (uint32_t i=0;i<parent.size();++i) parent[i]=i;
  auto root=[&](uint32_t i) { while(parent[i]!=i) { parent[i]=parent[parent[i]]; i=parent[i]; } return i; };
  for (const auto &f:a.faces) for(auto i:f.vertices) parent[root(i)]=root(f.vertices[0]);
  std::map<uint32_t,Mesh> parts;
  for (uint32_t i=0;i<a.vertices.size();++i) parts[root(i)].vertices.push_back(a.vertices[i]);
  for (const auto &part:parts)
  {
    Bounds bounds(part.second);
    if (!separated(bounds,b,false) && !zeroAreaContact(bounds,b)) return false;
  }
  return true;
}
Transform compose(const Transform &a,const Transform &b)
{
  Transform r;
  for (unsigned i=0;i<3;++i) r.column[i]=a.vector(b.column[i]);
  r.column[3]=a.point(b.column[3]); return r;
}
} // namespace
Result booleanOperation(const Mesh &a,const Mesh &b,Operation op,Id node,const Surface *cutOverride)
{
  Result result;
  if (!validate(a,result.diagnostics,node) || !validate(b,result.diagnostics,node)) return result;
  auto done=[&](Mesh mesh) {
    result.mesh=std::make_shared<Mesh>(std::move(mesh)); result.success=true; return result;
  };
  if (a.faces.empty()) return done(op==Operation::Union ? b:Mesh{});
  if (b.faces.empty()) return done(op==Operation::Intersect ? Mesh{}:a);
  Bounds ab(a),bb(b);
  if (separated(ab,bb,false) || zeroAreaContact(ab,bb) || componentsSeparate(a,bb))
    return done(op==Operation::Union ? concatenate(a,b) : op==Operation::Subtract ? a : Mesh{});
  if (op!=Operation::Union && separated(ab,bb,true)) return done(op==Operation::Subtract ? a:Mesh{});
  Vec origin=(ab.lo+ab.hi)*0.5;
  try
  {
    carve::csg::CSG backend;
    Attribute attributes; attributes.installHooks(backend);
    // Keep polygon boundaries through intermediate operations. Repeatedly
    // triangulating every boolean feeds internal diagonals into later cuts and
    // multiplies fragmentation. Tessellate only at the publication boundary.
    auto left=makePoly(a,origin,attributes,nullptr);
    auto right=makePoly(b,origin,attributes,op==Operation::Subtract ? cutOverride:nullptr);
    std::unique_ptr<Poly> out(backend.compute(left.get(),right.get(),op==Operation::Union ? carve::csg::CSG::UNION :
      op==Operation::Subtract ? carve::csg::CSG::A_MINUS_B : carve::csg::CSG::INTERSECTION,nullptr,carve::csg::CSG::CLASSIFY_EDGE));
    ++result.booleanCalls;
    if (!out) throw std::runtime_error("Carve returned no result");
    Mesh mesh;
    // Map by vertex identity, not position: touching components must not weld.
    std::map<const Poly::vertex_t *,uint32_t> vertices;
    for (auto it=out->faceBegin();it!=out->faceEnd();++it)
    {
      auto *face=*it;
      Face f=attributes.getAttribute(face,Face{});
      f.vertices.clear();
      std::vector<Poly::vertex_t *> fv; face->getVertices(fv);
      for (auto *v:fv)
      {
        auto inserted=vertices.emplace(v,uint32_t(vertices.size()));
        if (inserted.second) mesh.vertices.push_back(Vec{v->v[0],v->v[1],v->v[2]}+origin);
        f.vertices.push_back(inserted.first->second);
      }
      // Carve represents a planar face containing a hole as a weakly simple
      // contour: a bridge is traversed twice, repeating its endpoint vertices.
      // Our saved/evaluated faces are simple polygons. Resolve only these
      // contours through Carve's own projected triangulator; ordinary faces
      // remain polygons so later operations do not intersect needless diagonals.
      std::set<uint32_t> unique(f.vertices.begin(),f.vertices.end());
      if(unique.size()!=f.vertices.size())
      {
        std::vector<carve::triangulate::tri_idx> triangles;
        carve::triangulate::triangulate(Poly::face_t::projection_mapping(face->project),fv,triangles);
        for(auto triangle:triangles)
        {
          Face piece=f;
          piece.vertices={f.vertices[triangle.a],f.vertices[triangle.b],f.vertices[triangle.c]};
          if(piece.vertices[0]==piece.vertices[1] || piece.vertices[1]==piece.vertices[2] || piece.vertices[2]==piece.vertices[0])
            continue; // The doubled bridge has zero area, not a solid surface.
          mesh.faces.push_back(std::move(piece));
        }
      }
      else mesh.faces.push_back(std::move(f));
    }
    if (!validate(mesh,result.diagnostics,node)) return result;
    return done(std::move(mesh));
  }
  catch (const carve::exception &e) { result.diagnostics.push_back({Code::BackendFailure,node,0,e.str()}); }
  catch (const std::exception &e) { result.diagnostics.push_back({Code::BackendFailure,node,0,e.what()}); }
  catch (...) { result.diagnostics.push_back({Code::BackendFailure,node,0,"Unknown Carve exception"}); }
  return result;
}
std::shared_ptr<const Mesh> Evaluator::evaluateNode(const Node &n,const Transform &parent,Result &result)
{
  if (!n.visible) return std::make_shared<Mesh>();
  Transform tm=compose(parent,n.transform);
  uint64_t hash=fingerprint(n);
  // Parent transforms are dependencies too, including texture locking.
  Node transformKey; transformKey.transform=tm; hash^=fingerprint(transformKey);
  auto found=cache.find(n.id);
  if (found!=cache.end() && found->second.hash==hash) { ++result.cacheHits; return found->second.mesh; }
  std::shared_ptr<const Mesh> mesh;
  if (!n.brush.faces.empty())
  {
    if (!validate(n.brush,result.diagnostics,n.id,true)) return {};
    if (!std::isfinite(tm.determinant()) || std::abs(tm.determinant())<1e-15)
    { result.diagnostics.push_back({Code::InvalidMesh,n.id,0,"Singular or non-finite brush transform"}); return {}; }
    auto transformedMesh=std::make_shared<Mesh>(transformed(n.brush,tm));
    if (!validate(*transformedMesh,result.diagnostics,n.id)) return {};
    mesh=std::move(transformedMesh);
  }
  else mesh=std::make_shared<Mesh>();
  // A collection of pairwise disjoint additive solids needs no boolean work.
  // Testing only the accumulated AABB is insufficient: it encloses the empty
  // spaces between prior components and sends unrelated brushes through Carve.
  if (n.brush.faces.empty() && n.children.size()>1)
  {
    bool additive=true;
    for (const auto &child:n.children) if (child.visible && child.operation!=Operation::Union) additive=false;
    if (additive)
    {
      std::vector<std::shared_ptr<const Mesh>> parts;
      std::vector<Bounds> bounds;
      bool disjoint=true;
      for (const auto &child:n.children)
      {
        if (!child.visible) continue;
        auto part=evaluateNode(child,tm,result); if (!part) return {};
        if (part->faces.empty()) continue;
        Bounds bound(*part);
        for (const auto &previous:bounds) if (!separated(previous,bound,false)) { disjoint=false; break; }
        bounds.push_back(bound); parts.push_back(part);
      }
      if (disjoint)
      {
        auto joined=std::make_shared<Mesh>();
        size_t vertices=0,faces=0;
        for (const auto &part:parts) { vertices+=part->vertices.size(); faces+=part->faces.size(); }
        joined->vertices.reserve(vertices); joined->faces.reserve(faces);
        for (const auto &part:parts)
        {
          uint32_t offset=uint32_t(joined->vertices.size());
          joined->vertices.insert(joined->vertices.end(),part->vertices.begin(),part->vertices.end());
          for (auto face:part->faces) { for (auto &index:face.vertices) index+=offset; joined->faces.push_back(std::move(face)); }
        }
        cache[n.id]={hash,joined}; return joined;
      }
    }
  }
  Node base=n; base.children.clear();
  uint64_t prefixHash=fingerprint(base)^fingerprint(transformKey);
  auto &savedPrefixes=prefixes[n.id];
  size_t prefixIndex=0;
  for (const auto &child:n.children)
  {
    if (!child.visible) continue;
    prefixHash^=fingerprint(child)+0x9e3779b97f4a7c15ULL+(prefixHash<<6)+(prefixHash>>2);
    if(prefixIndex<savedPrefixes.size() && savedPrefixes[prefixIndex].hash==prefixHash)
    { mesh=savedPrefixes[prefixIndex++].mesh; ++result.cacheHits; continue; }
    auto next=evaluateNode(child,tm,result); if (!next) return {};
    Surface cutOverride;
    if(child.overrideCutSurface) cutOverride=transformedSurface(child.cutSurface,compose(tm,child.transform));
    auto combined=booleanOperation(*mesh,*next,child.operation,child.id,child.overrideCutSurface ? &cutOverride:nullptr);
    result.booleanCalls+=combined.booleanCalls;
    if (!combined.success)
    { result.diagnostics.insert(result.diagnostics.end(),combined.diagnostics.begin(),combined.diagnostics.end()); return {}; }
    mesh=combined.mesh;
    if(prefixIndex==savedPrefixes.size()) savedPrefixes.push_back({prefixHash,mesh});
    else savedPrefixes[prefixIndex]={prefixHash,mesh};
    ++prefixIndex;
  }
  savedPrefixes.resize(prefixIndex);
  cache[n.id]={hash,mesh}; return mesh;
}
Result Evaluator::evaluate(const Document &doc)
{
  Result result; result.revision=++revision;
  std::set<Id> ids,liveNodes;
  std::function<bool(const Node &,unsigned)> check=[&](const Node &n,unsigned depth) {
    auto fail=[&](const char *message) { result.diagnostics.push_back({Code::InvalidDocument,n.id,0,message}); return false; };
    if (depth>128) return fail("CSG hierarchy exceeds 128 levels");
    if (!n.id || n.id>=doc.nextId || !ids.insert(n.id).second) return fail("Invalid or duplicate node ID");
    liveNodes.insert(n.id);
    if (!n.brush.faces.empty() && !n.children.empty()) return fail("Brushes cannot also contain child operations");
    for (const auto &f:n.brush.faces)
      if (!f.id || f.id>=doc.nextId || !ids.insert(f.id).second || f.sourceBrush!=n.id) return fail("Invalid surface identity");
    for (const auto &c:n.children) if (!check(c,depth+1)) return false;
    return true;
  };
  if (!check(doc.root,0)) return result;
  for (auto it=cache.begin();it!=cache.end();) if (!liveNodes.count(it->first)) it=cache.erase(it); else ++it;
  for(auto it=prefixes.begin();it!=prefixes.end();) if(!liveNodes.count(it->first)) it=prefixes.erase(it); else ++it;
  result.mesh=evaluateNode(doc.root,Transform{},result);
  result.success=bool(result.mesh);
  if (result.success) published=result;
  return result;
}
void Evaluator::clear() { cache.clear(); prefixes.clear(); published=Result{}; revision=0; }
bool triangulateForPublication(const Mesh &source,Mesh &output,Diagnostics &errors)
{
  Mesh result; result.vertices=source.vertices;
  try
  {
    for(const auto &face:source.faces)
    {
      Vec origin=source.vertices[face.vertices[0]],normal{};
      for(size_t i=1;i+1<face.vertices.size();++i)
        normal=normal+cross(source.vertices[face.vertices[i]]-origin,source.vertices[face.vertices[i+1]]-origin);
      normal=normalized(normal);
      Vec u=normalized(source.vertices[face.vertices[1]]-origin),v=cross(normal,u);
      std::vector<carve::geom2d::P2> polygon;
      for(auto i:face.vertices) { auto p=source.vertices[i]-origin; polygon.push_back(carve::geom::VECTOR(dot(p,u),dot(p,v))); }
      std::vector<carve::triangulate::tri_idx> triangles;
      carve::triangulate::triangulate(polygon,triangles);
      // Preserve collinear boundary vertices. Ear clipping can leave a final
      // zero-area triangle A-M-B; dropping it would create a T-junction with
      // the adjacent face. Split the triangle across its longest edge instead,
      // replacing A-B-D with A-M-D and M-B-D without changing the boundary.
      for(size_t pass=0;pass<triangles.size()*triangles.size();++pass)
      {
        bool changed=false;
        for(size_t ti=0;ti<triangles.size() && !changed;++ti)
        {
          auto t=triangles[ti]; uint32_t p[3]={t.a,t.b,t.c};
          auto position=[&](uint32_t i) { return source.vertices[face.vertices[i]]; };
          if(length(cross(position(p[1])-position(p[0]),position(p[2])-position(p[0])))!=0) continue;
          int longest=0;
          for(int i=1;i<3;++i)
            if(length(position(p[i])-position(p[(i+1)%3]))>length(position(p[longest])-position(p[(longest+1)%3]))) longest=i;
          auto a=p[longest],b=p[(longest+1)%3],middle=p[(longest+2)%3];
          for(size_t other=0;other<triangles.size() && !changed;++other)
          {
            if(other==ti) continue;
            auto n=triangles[other]; uint32_t q[3]={n.a,n.b,n.c};
            for(int edge=0;edge<3;++edge)
              if(q[edge]==b && q[(edge+1)%3]==a)
              {
                auto d=q[(edge+2)%3];
                if(length(cross(position(middle)-position(b),position(d)-position(b)))==0 ||
                   length(cross(position(a)-position(middle),position(d)-position(middle)))==0) continue;
                triangles[other]=carve::triangulate::tri_idx(b,middle,d);
                triangles[ti]=carve::triangulate::tri_idx(middle,a,d);
                changed=true; break;
              }
          }
        }
        if(!changed) break;
      }
      for(auto t:triangles)
      { Face f=face; f.vertices={face.vertices[t.a],face.vertices[t.b],face.vertices[t.c]}; result.faces.push_back(std::move(f)); }
    }
    if(!validate(result,errors)) return false;
    output=std::move(result); return true;
  }
  catch(...) { errors.push_back({Code::InvalidResult,0,0,"Publication triangulation failed"}); return false; }
}
} // namespace csg
