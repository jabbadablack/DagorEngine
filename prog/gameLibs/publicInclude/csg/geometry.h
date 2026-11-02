// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once

// Authoring data is independent of renderer meshes. All modelling is performed
// in doubles; conversion to engine floats happens only at publication.
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>

namespace csg
{
using Id = uint64_t;
struct Vec
{
  double x = 0, y = 0, z = 0;
  Vec operator+(Vec b) const { return {x + b.x, y + b.y, z + b.z}; }
  Vec operator-(Vec b) const { return {x - b.x, y - b.y, z - b.z}; }
  Vec operator*(double s) const { return {x * s, y * s, z * s}; }
  Vec operator/(double s) const { return *this * (1 / s); }
};
double dot(Vec a, Vec b);
Vec cross(Vec a, Vec b);
double length(Vec a);
Vec normalized(Vec a);
bool finite(Vec a);
struct Transform
{
  std::array<Vec, 4> column = {{{1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {0, 0, 0}}};
  Vec vector(Vec v) const;
  Vec point(Vec v) const { return vector(v) + column[3]; }
  Vec inversePoint(Vec v) const;
  double determinant() const;
};
struct Surface
{
  std::string material;
  Vec u = {1, 0, 0}, v = {0, 0, 1};
  double scaleU = 1, scaleV = 1, offsetU = 0, offsetV = 0, rotation = 0;
  bool worldLocked = false;
  uint32_t smoothing = 0;
};
struct Face
{
  Id id = 0, sourceBrush = 0;
  std::vector<uint32_t> vertices;
  Surface surface;
};
struct Mesh
{
  std::vector<Vec> vertices;
  std::vector<Face> faces;
};
enum class Operation { Union, Subtract, Intersect };
enum class Code { InvalidDocument, InvalidMesh, NonConvex, BackendFailure, InvalidResult };
struct Diagnostic
{
  Code code;
  Id node = 0, face = 0;
  std::string message;
};
using Diagnostics = std::vector<Diagnostic>;
enum class ExtrusionMode { Depth, Spin, Path };
struct CurvePoint
{
  Vec position, incoming, outgoing; // Cubic Bezier handles relative to position.
  double tilt = 0; // Radians about the path tangent.
};
struct Extrusion
{
  struct FaceSettings { Surface surface; bool automaticUv = true; };
  ExtrusionMode mode = ExtrusionMode::Depth;
  std::vector<Vec> polygon; // XY profile, Z must be zero; simple concave profiles are supported.
  double depth = 1, spinDegrees = 360;
  unsigned spinSides = 32, pathSubdivisions = 8;
  std::vector<CurvePoint> path;
  bool pathJoined = false;
  Surface surface;
  // Optional logical surfaces: front, back, then profile edges. These slots
  // correspond to Node::extrusionSurfaces and survive parameter-only edits.
  std::vector<FaceSettings> surfaces;
};
// Transactional, renderer-independent generator shared by editor and runtime.
// Invalid/self-intersecting sweeps fail without replacing output.
bool generateExtrusion(const Extrusion &source, Mesh &output, Diagnostics &errors);
bool validateClosedMesh(const Mesh &mesh,Diagnostics &errors);
bool mapSurfaceTriangle(Surface &surface,Vec a,Vec b,Vec c,Vec uv0,Vec uv1,Vec uv2);
struct Node
{
  Id id = 0;
  std::string name;
  Operation operation = Operation::Union;
  bool visible = true;
  Transform transform;
  Mesh brush; // Empty for an operation group.
  bool closedMesh = false; // Explicit imported closed source; component edits remain convex-brush-only.
  std::string meshSource;
  std::vector<Node> children;
  bool overrideCutSurface = false;
  Surface cutSurface;
  bool parametric = false;
  Extrusion extrusion;
  std::vector<Id> extrusionSurfaces; // Front, back, then one stable ID per profile edge.
};
struct Document
{
  static constexpr int VERSION = 2;
  Id nextId = 1;
  bool runtimeEditable = true; // Source-backed publication; legacy box/occluder records remain separate.
  Node root;
  Id allocate() { return nextId++; }
  Node *find(Id id);
  const Node *find(Id id) const;
  void assignIds(Node &node);
};
struct ResultChunk
{
  uint64_t hash = 0;
  std::shared_ptr<const Mesh> mesh;
};
struct Result
{
  bool success = false;
  std::shared_ptr<const Mesh> mesh;
  std::vector<ResultChunk> chunks; // Optional immutable disjoint subresults, reusable by publishers.
  Diagnostics diagnostics;
  uint64_t revision = 0;
  size_t booleanCalls = 0, cacheHits = 0;
};

// Empty results are valid. Nonempty solids must be closed and consistently
// oriented. Convexity is an authoring restriction, not a prefab restriction.
bool validate(const Mesh &mesh, Diagnostics &errors, Id node = 0, bool convex = false);
double volume(const Mesh &mesh);
bool triangulateForPublication(const Mesh &source, Mesh &output, Diagnostics &errors);
bool prepareFloatPublication(const Mesh &source,Mesh &output,Vec &origin,Diagnostics &errors);
uint64_t fingerprint(const Node &node,bool include_children = true);
Mesh transformed(const Mesh &mesh, const Transform &transform);
Surface transformedSurface(const Surface &surface, const Transform &transform);
Mesh box(Vec size);
Mesh ramp(Vec size);
Mesh cylinder(double radius, double height, unsigned sides);
bool moveVertices(Mesh &mesh, const std::vector<uint32_t> &vertices, Vec delta, Diagnostics &errors);
bool clip(Mesh &mesh, Vec normal, double distance, Id new_face, const Surface &surface, Diagnostics &errors);
bool bevel(Mesh &mesh, const std::vector<uint32_t> &vertices, double distance, Id new_face, Diagnostics &errors);
bool extrudeFace(const Mesh &mesh, size_t face, double distance, Mesh &prism, Diagnostics &errors);
bool extrudeOutline(const std::vector<Vec> &outline, Vec displacement, std::vector<Mesh> &prisms, Diagnostics &errors);
void alignSurface(Surface &target, const Surface &source);
std::array<double, 2> textureCoordinates(const Surface &surface, Vec position);

// Serial evaluator: Carve EPSILON and Dagor's unwrap API have process-global
// state. Cached inputs and intermediate results are immutable.
class Evaluator
{
public:
  Result evaluate(const Document &document);
  void clear();
  const Result &lastValid() const { return published; }
private:
  struct Entry { uint64_t hash; std::shared_ptr<const Mesh> mesh; std::vector<ResultChunk> chunks; };
  std::unordered_map<Id, Entry> cache;
  std::unordered_map<Id, std::vector<Entry>> prefixes;
  std::unordered_map<Id, uint64_t> inputHashes;
  std::vector<std::shared_ptr<Mesh>> aggregateBuffers;
  Result published;
  uint64_t revision = 0;
  std::shared_ptr<const Mesh> evaluateNode(const Node &node, const Transform &parent, Result &result);
  uint64_t hashNode(const Node &node);
  Id rootId = 0;
};
// Shared by the document evaluator and regression tests. Both inputs remain
// unchanged. Cut surfaces preserve source attribution even when overridden.
Result booleanOperation(const Mesh &a, const Mesh &b, Operation operation, Id node = 0, const Surface *cut_override = nullptr);
} // namespace csg
