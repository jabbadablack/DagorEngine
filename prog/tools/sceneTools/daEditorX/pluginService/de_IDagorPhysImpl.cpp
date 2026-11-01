// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include "de_IDagorPhysImpl.h"

#include <oldEditor/de_collision.h>

#include <gameRes/dag_collisionResource.h>
#include <math/dag_capsule.h>
#include <libTools/staticGeom/staticGeometryContainer.h>
#include <phys/dag_physics.h>
#ifdef USE_JOLT_PHYSICS
#include <Jolt/Physics/Collision/Shape/MeshShape.h>
#endif

void *DeDagorPhys::prepare(const StaticGeometryContainer &container)
{
#ifdef USE_JOLT_PHYSICS
  Tab<Point3> vertices(tmpmem); Tab<int> indices(tmpmem);
  for(const auto *node:container.nodes)
  {
    if(!node->mesh || !(node->flags&StaticGeometryNode::FLG_COLLIDABLE)) continue;
    const auto &mesh=node->mesh->mesh;
    int base=vertices.size();
    for(auto vertex:mesh.vert) vertices.push_back(node->wtm*vertex);
    for(const auto &face:mesh.face) for(auto index:face.v) indices.push_back(base+index);
  }
  if(indices.empty()) return nullptr;
  // Same public Jolt cooking path used by PhysBody's triangle-mesh adapter.
  JPH::MeshShapeSettings input;
  for(auto vertex:vertices) input.mTriangleVertices.emplace_back(vertex.x,vertex.y,vertex.z);
  for(int i=0;i<indices.size();i+=3) input.mIndexedTriangles.emplace_back(indices[i],indices[i+1],indices[i+2]);
  auto cooked=input.Create();
  if(!cooked.IsValid()) return nullptr;
  // A cooked immutable shape has no dependency on a particular world's body
  // lifetime, so it remains safe across the embedded game's scene reloads.
  return new JPH::RefConst<JPH::Shape>(cooked.Get());
#else
  return nullptr;
#endif
}
void DeDagorPhys::release(void *value)
{
#ifdef USE_JOLT_PHYSICS
  delete static_cast<JPH::RefConst<JPH::Shape> *>(value);
#endif
}


//==================================================================================================
bool DeDagorPhys::traceRayStatic(const Point3 &p, const Point3 &dir, real &maxt) const
{
  return DagorPhys::trace_ray_static(p, dir, maxt);
}


//==================================================================================================
bool DeDagorPhys::traceRayStatic(const Point3 &p, const Point3 &dir, real &maxt, Point3 &norm) const
{
  return DagorPhys::trace_ray_static(p, dir, maxt, norm);
}


//==================================================================================================
bool DeDagorPhys::rayHitStatic(const Point3 &p, const Point3 &dir, real maxt) const { return DagorPhys::ray_hit_static(p, dir, maxt); }


//==================================================================================================
real DeDagorPhys::clipCapsuleStatic(Capsule &c, Point3 &cap_pt, Point3 &world_pt) const
{
  return DagorPhys::clip_capsule_static(c, cap_pt, world_pt);
}


//==================================================================================================
void DeDagorPhys::visitClipTriangles(const BBox3 &box, const ClipTriVisitor &visitor) const
{
  const CollisionResource *clip = DagorPhys::getClipCollision();
  if (!clip)
    return;

  clip->visitTrianglesInBox(v_ldu_bbox3(box), CollisionNode::TRACEABLE, [&visitor](vec3f a, vec3f b, vec3f c, int, int) {
    Point3 v0, v1, v2;
    v_stu_p3(&v0.x, a), v_stu_p3(&v1.x, b), v_stu_p3(&v2.x, c);
    visitor(v0, v1, v2);
    return false;
  });
}


//==================================================================================================
void DeDagorPhys::closeCollision() const { DagorPhys::close_collision(); }


//==================================================================================================
BBox3 DeDagorPhys::getBoundingBox() const { return DagorPhys::get_bounding_box(); }
