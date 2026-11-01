// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
class StaticGeometryContainer;
class ICsgCollisionPreparation
{
public:
  static constexpr unsigned HUID = 0x43534750;
  virtual void *prepare(const StaticGeometryContainer &) = 0;
  virtual void release(void *) = 0;
};
