// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <csg/geometry.h>
class DataBlock;
namespace csg
{
void saveDocument(const Document &document, DataBlock &block);
void saveSourceNode(const Node &node, DataBlock &block);
bool loadDocument(const DataBlock &block, Document &document, Diagnostics &diagnostics);
}
