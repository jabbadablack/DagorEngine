// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
#include <libTools/CSG/brush.h>
class DataBlock;
namespace csg
{
void saveDocument(const Document &document, DataBlock &block);
bool loadDocument(const DataBlock &block, Document &document, Diagnostics &diagnostics);
}
