// Copyright (C) Gaijin Games KFT. All rights reserved.
#include <libTools/CSG/brush.h>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>
#include <map>
#include <set>

namespace csg
{
double dot(Vec a, Vec b) { return a.x * b.x + a.y * b.y + a.z * b.z; }
Vec cross(Vec a, Vec b) { return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x}; }
double length(Vec a) { return std::sqrt(dot(a, a)); }
Vec normalized(Vec a) { double l = length(a); return l > 0 ? a / l : Vec{}; }
bool finite(Vec a) { return std::isfinite(a.x) && std::isfinite(a.y) && std::isfinite(a.z); }
Vec Transform::vector(Vec a) const { return column[0] * a.x + column[1] * a.y + column[2] * a.z; }
double Transform::determinant() const { return dot(column[0], cross(column[1], column[2])); }
Vec Transform::inversePoint(Vec p) const
{
  p = p - column[3];
  double d = determinant();
  return {dot(p, cross(column[1], column[2])) / d, dot(p, cross(column[2], column[0])) / d,
    dot(p, cross(column[0], column[1])) / d};
}
static Node *findNode(Node &n, Id id)
{
  if (n.id == id) return &n;
  for (auto &c : n.children) if (auto *p = findNode(c, id)) return p;
  return nullptr;
}
Node *Document::find(Id id) { return findNode(root, id); }
const Node *Document::find(Id id) const { return findNode(const_cast<Node &>(root), id); }
void Document::assignIds(Node &n)
{
  n.id = allocate();
  for (auto &f : n.brush.faces) { f.id = allocate(); f.sourceBrush = n.id; }
  for (auto &c : n.children) assignIds(c);
}
static Vec faceNormal(const Mesh &m, const Face &f)
{
  Vec n{}, origin = m.vertices[f.vertices[0]];
  for (size_t i = 1; i + 1 < f.vertices.size(); ++i)
    n = n + cross(m.vertices[f.vertices[i]] - origin, m.vertices[f.vertices[i + 1]] - origin);
  return normalized(n);
}
double volume(const Mesh &m)
{
  if (m.vertices.empty()) return 0;
  double v = 0;
  Vec o = m.vertices[0];
  for (const auto &f : m.faces)
    for (size_t i = 1; i + 1 < f.vertices.size(); ++i)
      v += dot(m.vertices[f.vertices[0]] - o,
        cross(m.vertices[f.vertices[i]] - o, m.vertices[f.vertices[i + 1]] - o)) / 6;
  return v;
}
bool validate(const Mesh &m, Diagnostics &errors, Id node, bool convex)
{
  auto fail = [&](Code code, Id face, const char *text) { errors.push_back({code, node, face, text}); return false; };
  if (m.faces.empty()) return m.vertices.empty() || fail(Code::InvalidMesh, 0, "Vertices without solid faces");
  double extent = 0;
  for (Vec p : m.vertices)
  {
    if (!finite(p)) return fail(Code::InvalidMesh, 0, "Non-finite vertex");
    extent = std::max(extent, length(p - m.vertices[0]));
  }
  // Numerical validation tolerance, deliberately much smaller than the 1 cm
  // authoring envelope. It never modifies Carve's global epsilon.
  const double tolerance = std::max(1e-10, extent * 1e-10);
  std::map<std::pair<uint32_t, uint32_t>, unsigned> edges;
  std::set<Id> ids;
  for (const auto &f : m.faces)
  {
    if (f.vertices.size() < 3) return fail(Code::InvalidMesh, f.id, "Face has fewer than three vertices");
    std::set<uint32_t> unique;
    for (uint32_t i : f.vertices)
      if (i >= m.vertices.size() || !unique.insert(i).second)
        return fail(Code::InvalidMesh, f.id, "Invalid or repeated face vertex");
    Vec n = faceNormal(m, f);
    if (length(n) < 0.5) return fail(Code::InvalidMesh, f.id, "Degenerate face");
    const Vec origin = m.vertices[f.vertices[0]];
    for (uint32_t i : f.vertices)
      if (std::abs(dot(n, m.vertices[i] - origin)) > tolerance)
        return fail(Code::InvalidMesh, f.id, "Non-planar face");
    if (!finite(f.surface.u) || !finite(f.surface.v) || !std::isfinite(f.surface.scaleU) ||
        !std::isfinite(f.surface.scaleV) || std::abs(f.surface.scaleU) < 1e-12 || std::abs(f.surface.scaleV) < 1e-12 ||
        !std::isfinite(f.surface.rotation) || !std::isfinite(f.surface.offsetU) || !std::isfinite(f.surface.offsetV))
      return fail(Code::InvalidMesh, f.id, "Invalid surface mapping");
    for (size_t i = 0; i < f.vertices.size(); ++i)
    {
      auto edge = std::make_pair(f.vertices[i], f.vertices[(i + 1) % f.vertices.size()]);
      if (length(m.vertices[edge.first] - m.vertices[edge.second]) <= tolerance || ++edges[edge] != 1)
        return fail(Code::InvalidMesh, f.id, "Collapsed or multiply directed edge");
      if (convex)
      {
        Vec a = m.vertices[edge.first], b = m.vertices[edge.second];
        Vec c = m.vertices[f.vertices[(i + 2) % f.vertices.size()]];
        if (dot(cross(b - a, c - b), n) < -tolerance * tolerance)
          return fail(Code::NonConvex, f.id, "Non-convex face");
      }
    }
    if (convex)
      for (Vec p : m.vertices)
        if (dot(n, p - origin) > tolerance)
          return fail(Code::NonConvex, f.id, "Edit would make the brush concave or invert a face");
  }
  for (const auto &e : edges)
    if (!edges.count({e.first.second, e.first.first})) return fail(Code::InvalidMesh, 0, "Open or inconsistently wound solid");
  if (!(volume(m) > tolerance * tolerance * tolerance)) return fail(Code::InvalidMesh, 0, "Solid has no positive volume");
  return true;
}
Surface transformedSurface(const Surface &source,const Transform &t)
{
  Surface result=source;
  const double d = t.determinant();
  if (!result.worldLocked && d != 0)
  {
      auto covector = [&](Vec v) {
        return (cross(t.column[1], t.column[2]) * v.x + cross(t.column[2], t.column[0]) * v.y +
          cross(t.column[0], t.column[1]) * v.z) / d;
      };
      Vec u = covector(result.u), v = covector(result.v);
      // Translation is applied before rotation in textureCoordinates.
      double angle = result.rotation * 3.14159265358979323846 / 180;
      double du = dot(u, t.column[3]), dv = dot(v, t.column[3]);
      result.offsetU -= (du * std::cos(angle) - dv * std::sin(angle)) / result.scaleU;
      result.offsetV -= (du * std::sin(angle) + dv * std::cos(angle)) / result.scaleV;
      result.u = u; result.v = v;
  }
  return result;
}
Mesh transformed(const Mesh &m, const Transform &t)
{
  Mesh result=m;
  for(auto &p:result.vertices) p=t.point(p);
  for(auto &face:result.faces)
  {
    if(t.determinant()<0) std::reverse(face.vertices.begin(),face.vertices.end());
    face.surface=transformedSurface(face.surface,t);
  }
  return result;
}
static Mesh primitive(std::vector<Vec> vertices, std::vector<std::vector<uint32_t>> faces)
{
  Mesh m; m.vertices = std::move(vertices);
  Vec center{}; for (Vec p : m.vertices) center = center + p; center = center / double(m.vertices.size());
  for (auto indices : faces)
  {
    Face f; f.id = m.faces.size() + 1; f.vertices = std::move(indices);
    if (dot(faceNormal(m, f), m.vertices[f.vertices[0]] - center) < 0) std::reverse(f.vertices.begin(), f.vertices.end());
    Vec n = faceNormal(m, f);
    f.surface.u = normalized(cross(std::abs(n.y) < 0.9 ? Vec{0, 1, 0} : Vec{0, 0, 1}, n));
    f.surface.v = cross(n, f.surface.u);
    m.faces.push_back(std::move(f));
  }
  return m;
}
Mesh box(Vec s)
{
  s = s * 0.5;
  return primitive({{-s.x,-s.y,-s.z},{s.x,-s.y,-s.z},{s.x,s.y,-s.z},{-s.x,s.y,-s.z},
    {-s.x,-s.y,s.z},{s.x,-s.y,s.z},{s.x,s.y,s.z},{-s.x,s.y,s.z}},
    {{0,1,2,3},{4,7,6,5},{0,4,5,1},{3,2,6,7},{0,3,7,4},{1,5,6,2}});
}
Mesh ramp(Vec s)
{
  return primitive({{0,0,0},{s.x,0,0},{0,s.y,0},{0,0,s.z},{s.x,0,s.z},{0,s.y,s.z}},
    {{0,1,2},{3,5,4},{0,3,4,1},{1,4,5,2},{0,2,5,3}});
}
Mesh cylinder(double radius, double height, unsigned sides)
{
  if (sides < 3 || sides > 4096 || !(radius > 0) || !(height > 0)) return {};
  std::vector<Vec> vertices;
  std::vector<std::vector<uint32_t>> faces(2);
  for (unsigned y = 0; y < 2; ++y)
    for (unsigned i = 0; i < sides; ++i)
    {
      double a = i * 6.28318530717958647692 / sides;
      vertices.push_back({radius * std::cos(a), y * height, radius * std::sin(a)});
      faces[y].push_back(y * sides + i);
    }
  for (unsigned i = 0; i < sides; ++i) faces.push_back({i, (i+1)%sides, (i+1)%sides+sides, i+sides});
  return primitive(std::move(vertices), std::move(faces));
}
bool moveVertices(Mesh &m, const std::vector<uint32_t> &indices, Vec delta, Diagnostics &errors)
{
  Mesh candidate = m;
  std::set<uint32_t> unique(indices.begin(), indices.end());
  for (auto i : unique)
  {
    if (i >= m.vertices.size()) { errors.push_back({Code::InvalidMesh,0,0,"Selected vertex no longer exists"}); return false; }
    candidate.vertices[i] = candidate.vertices[i] + delta;
  }
  if (!validate(candidate, errors, 0, true)) return false;
  m = std::move(candidate); return true;
}
bool clip(Mesh &m, Vec n, double d, Id faceId, const Surface &surface, Diagnostics &errors)
{
  double l = length(n);
  if (!(l > 0) || !std::isfinite(d)) { errors.push_back({Code::InvalidMesh,0,0,"Invalid clip plane"}); return false; }
  n = n / l; d /= l;
  Mesh result; result.vertices = m.vertices;
  std::map<std::pair<uint32_t,uint32_t>,uint32_t> intersections;
  std::set<uint32_t> cap;
  constexpr double eps = 1e-10;
  auto intersection = [&](uint32_t a, uint32_t b, double da, double db) {
    if (std::abs(da) <= eps) { cap.insert(a); return a; }
    if (std::abs(db) <= eps) { cap.insert(b); return b; }
    auto key = std::minmax(a,b);
    auto found = intersections.find(key);
    if (found != intersections.end()) return found->second;
    uint32_t index = uint32_t(result.vertices.size());
    result.vertices.push_back(m.vertices[a] + (m.vertices[b]-m.vertices[a]) * (da/(da-db)));
    intersections[key] = index; cap.insert(index); return index;
  };
  for (const auto &face : m.faces)
  {
    Face f = face; f.vertices.clear();
    for (size_t i = 0; i < face.vertices.size(); ++i)
    {
      uint32_t a = face.vertices[i], b = face.vertices[(i+1)%face.vertices.size()];
      double da = dot(n,m.vertices[a])-d, db = dot(n,m.vertices[b])-d;
      if (da <= eps) f.vertices.push_back(a);
      if ((da < -eps && db > eps) || (da > eps && db < -eps) || (da > eps && std::abs(db) <= eps) ||
          (std::abs(da) <= eps && db > eps)) f.vertices.push_back(intersection(a,b,da,db));
    }
    f.vertices.erase(std::unique(f.vertices.begin(),f.vertices.end()),f.vertices.end());
    if (f.vertices.size() > 1 && f.vertices.front() == f.vertices.back()) f.vertices.pop_back();
    if (f.vertices.size() >= 3) result.faces.push_back(std::move(f));
  }
  if (cap.size() >= 3)
  {
    Face f; f.id = faceId; f.surface = surface;
    Vec center{}; for (auto i : cap) center = center + result.vertices[i]; center = center / double(cap.size());
    Vec u = normalized(cross(std::abs(n.y)<0.9 ? Vec{0,1,0} : Vec{0,0,1},n)), v = cross(n,u);
    f.vertices.assign(cap.begin(),cap.end());
    std::sort(f.vertices.begin(),f.vertices.end(),[&](uint32_t a,uint32_t b) {
      Vec pa = result.vertices[a]-center, pb = result.vertices[b]-center;
      return std::atan2(dot(pa,v),dot(pa,u)) < std::atan2(dot(pb,v),dot(pb,u));
    });
    result.faces.push_back(std::move(f));
  }
  // Compact before validation so clipped-away vertices cannot fail convexity.
  std::vector<uint32_t> remap(result.vertices.size(),UINT32_MAX);
  std::vector<Vec> vertices;
  for (auto &f : result.faces) for (auto &i : f.vertices)
  {
    if (remap[i] == UINT32_MAX) { remap[i] = uint32_t(vertices.size()); vertices.push_back(result.vertices[i]); }
    i = remap[i];
  }
  result.vertices = std::move(vertices);
  if (result.faces.empty()) { errors.push_back({Code::InvalidMesh,0,faceId,"Clip would remove the entire brush"}); return false; }
  if (!validate(result,errors,0,true)) return false;
  m = std::move(result); return true;
}
bool bevel(Mesh &m, const std::vector<uint32_t> &indices, double distance, Id faceId, Diagnostics &errors)
{
  if (indices.empty() || indices.size() > 2 || !(distance > 0)) return false;
  Vec n{}, p{};
  unsigned sharedFaces = 0;
  for (auto i : indices)
  {
    if (i >= m.vertices.size()) return false;
    p = p + m.vertices[i];
  }
  for (const auto &f : m.faces)
  {
    bool contains = true;
    for (auto i : indices) contains &= std::find(f.vertices.begin(),f.vertices.end(),i) != f.vertices.end();
    if (contains) { n = n + faceNormal(m,f); ++sharedFaces; }
  }
  if ((indices.size()==2 && (indices[0]==indices[1] || sharedFaces!=2)) || !sharedFaces)
  { errors.push_back({Code::InvalidMesh,0,0,"Bevel selection must be a vertex or an actual edge"}); return false; }
  n = normalized(n); p = p / double(indices.size());
  Surface s; s.u = normalized(cross(std::abs(n.y)<0.9 ? Vec{0,1,0}:Vec{0,0,1},n)); s.v = cross(n,s.u);
  return clip(m,n,dot(n,p)-distance,faceId,s,errors);
}
bool extrudeFace(const Mesh &m, size_t face, double distance, Mesh &prism, Diagnostics &errors)
{
  if (face >= m.faces.size() || !std::isfinite(distance) || std::abs(distance) < 1e-10) return false;
  const Face &f = m.faces[face];
  std::vector<Vec> vertices; std::vector<std::vector<uint32_t>> faces(2);
  unsigned count = unsigned(f.vertices.size()); Vec displacement = faceNormal(m,f) * distance;
  for (unsigned j = 0; j < 2; ++j) for (unsigned i = 0; i < count; ++i)
  {
    vertices.push_back(m.vertices[f.vertices[i]] + displacement * j); faces[j].push_back(j*count+i);
  }
  for (unsigned i=0;i<count;++i) faces.push_back({i,(i+1)%count,(i+1)%count+count,i+count});
  Mesh result = primitive(std::move(vertices),std::move(faces));
  for (auto &side : result.faces) side.surface.material = f.surface.material;
  result.faces[0].surface = f.surface; result.faces[1].surface = f.surface;
  if (!validate(result,errors,0,true)) return false;
  prism = std::move(result); return true;
}
static double orient(double ax,double ay,double bx,double by,double cx,double cy)
{ return (bx-ax)*(cy-ay)-(by-ay)*(cx-ax); }
bool extrudeOutline(const std::vector<Vec> &outline, Vec displacement, std::vector<Mesh> &prisms, Diagnostics &errors)
{
  auto fail = [&]() { errors.push_back({Code::InvalidMesh,0,0,"Outline must be simple, planar, nondegenerate and extruded out of its plane"}); return false; };
  if (outline.size()<3 || !finite(displacement)) return fail();
  for (Vec p : outline) if (!finite(p)) return fail();
  Vec n{}; for (size_t i=1;i+1<outline.size();++i) n = n + cross(outline[i]-outline[0],outline[i+1]-outline[0]);
  n = normalized(n); if (length(n)<0.5 || std::abs(dot(n,displacement))<1e-10) return fail();
  Vec u = normalized(outline[1]-outline[0]), v = cross(n,u);
  std::vector<std::array<double,2>> p;
  for (Vec a : outline)
  {
    a = a-outline[0]; if (std::abs(dot(a,n))>1e-9) return fail();
    p.push_back({dot(a,u),dot(a,v)});
  }
  auto side = [&](size_t a,size_t b,size_t c) { return orient(p[a][0],p[a][1],p[b][0],p[b][1],p[c][0],p[c][1]); };
  auto onSegment = [&](size_t a,size_t b,size_t c) {
    return std::abs(side(a,b,c))<=1e-12 && p[c][0]>=std::min(p[a][0],p[b][0])-1e-12 &&
      p[c][0]<=std::max(p[a][0],p[b][0])+1e-12 && p[c][1]>=std::min(p[a][1],p[b][1])-1e-12 &&
      p[c][1]<=std::max(p[a][1],p[b][1])+1e-12;
  };
  for (size_t a=0;a<p.size();++a)
  {
    size_t b=(a+1)%p.size(); if (length(outline[a]-outline[b])<1e-10) return fail();
    for (size_t c=a+1;c<p.size();++c)
    {
      size_t d=(c+1)%p.size(); if (a==d || b==c) continue;
      if ((side(a,b,c)*side(a,b,d)<0 && side(c,d,a)*side(c,d,b)<0) ||
          onSegment(a,b,c) || onSegment(a,b,d) || onSegment(c,d,a) || onSegment(c,d,b)) return fail();
    }
  }
  std::vector<uint32_t> ring; for (uint32_t i=0;i<p.size();++i) ring.push_back(i);
  std::vector<Mesh> result;
  while (ring.size()>2)
  {
    bool found=false;
    for (size_t i=0;i<ring.size();++i)
    {
      uint32_t a=ring[(i+ring.size()-1)%ring.size()], b=ring[i], c=ring[(i+1)%ring.size()];
      if (side(a,b,c)<=1e-12) continue;
      bool inside=false;
      for (auto d:ring) if (d!=a && d!=b && d!=c && side(a,b,d)>=-1e-12 && side(b,c,d)>=-1e-12 && side(c,a,d)>=-1e-12) inside=true;
      if (inside) continue;
      Mesh prism;
      // Extrusion direction can be oblique; construct the six vertices directly.
      prism = primitive({outline[a],outline[b],outline[c],outline[a]+displacement,outline[b]+displacement,outline[c]+displacement},
        {{0,1,2},{3,5,4},{0,3,4,1},{1,4,5,2},{2,5,3,0}});
      if (!validate(prism,errors,0,true)) return false;
      result.push_back(std::move(prism)); ring.erase(ring.begin()+i); found=true; break;
    }
    if (!found) return fail();
  }
  prisms = std::move(result); return true;
}
void alignSurface(Surface &target,const Surface &source)
{
  auto material=target.material; auto smoothing=target.smoothing;
  target=source; target.material=material; target.smoothing=smoothing;
}
std::array<double,2> textureCoordinates(const Surface &s,Vec p)
{
  double a=s.rotation*3.14159265358979323846/180, u=dot(s.u,p),v=dot(s.v,p);
  return {(u*std::cos(a)-v*std::sin(a))/s.scaleU+s.offsetU,(u*std::sin(a)+v*std::cos(a))/s.scaleV+s.offsetV};
}
static void hashBytes(uint64_t &h,const void *p,size_t n)
{ for (size_t i=0;i<n;++i) { h^=static_cast<const unsigned char *>(p)[i]; h*=1099511628211ULL; } }
template<class T> static void hashValue(uint64_t &h,const T &v) { hashBytes(h,&v,sizeof(v)); }
static void hashSurface(uint64_t &h,const Surface &s)
{
  hashValue(h,s.material.size()); hashBytes(h,s.material.data(),s.material.size());
  hashValue(h,s.u); hashValue(h,s.v); hashValue(h,s.scaleU); hashValue(h,s.scaleV);
  hashValue(h,s.offsetU); hashValue(h,s.offsetV); hashValue(h,s.rotation); hashValue(h,s.worldLocked); hashValue(h,s.smoothing);
}
uint64_t fingerprint(const Node &n)
{
  uint64_t h=14695981039346656037ULL;
  hashValue(h,n.id); hashValue(h,n.operation); hashValue(h,n.visible); hashValue(h,n.transform.column);
  hashValue(h,n.brush.vertices.size()); for (auto p:n.brush.vertices) hashValue(h,p);
  hashValue(h,n.brush.faces.size());
  for (const auto &f:n.brush.faces)
  {
    hashValue(h,f.id); hashValue(h,f.sourceBrush); hashValue(h,f.vertices.size());
    for (auto v:f.vertices) hashValue(h,v); hashSurface(h,f.surface);
  }
  hashValue(h,n.overrideCutSurface); if (n.overrideCutSurface) hashSurface(h,n.cutSurface);
  hashValue(h,n.children.size()); for (const auto &c:n.children) { auto ch=fingerprint(c); hashValue(h,ch); }
  return h;
}
} // namespace csg
