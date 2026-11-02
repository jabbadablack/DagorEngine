// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
class StaticGeometryContainer;
// Optional host service: reuse native primitive builders without linking their
// material/texture resource state into plugin DLLs.
class IEditorPrimitiveGeometry
{
public:
  static constexpr unsigned HUID=0x43534747;
  enum Kind { Sphere };
  virtual bool generate(Kind kind,int segments,StaticGeometryContainer &output)=0;
};
