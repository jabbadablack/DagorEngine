// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <csg/geometry.h>
#include <functional>

namespace csg
{
// Session-owned CSG state. Call serially on one owner thread. The publisher
// prepares render/collision/navigation resources and returns true only when it
// can publish them together. A rejected update retains the previous revision.
// Portal placement, rendering and traversal belong to the game using this API.
class RuntimeModel
{
public:
  using Publisher=std::function<bool(const Result &)>;
  RuntimeModel();
  const Document &document() const { return source; }
  const Result &result() const { return published; }
  bool commit(Document candidate,const Publisher &publish,Diagnostics &errors);
private:
  Document source;
  Result published;
  Evaluator evaluator;
  bool updating=false;
};
}
