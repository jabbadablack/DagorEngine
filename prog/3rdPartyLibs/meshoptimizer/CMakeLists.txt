# meshoptimizer: vertex cache, overdraw and fetch optimization, simplification
set(sources
  src/allocator.cpp
  src/clusterizer.cpp
  src/indexcodec.cpp
  src/indexgenerator.cpp
  src/meshletcodec.cpp
  src/meshletutils.cpp
  src/overdrawanalyzer.cpp
  src/overdrawoptimizer.cpp
  src/partition.cpp
  src/simplifier.cpp
  src/spatialorder.cpp
  src/stripifier.cpp
  src/vcacheanalyzer.cpp
  src/vcacheoptimizer.cpp
  src/vertexcodec.cpp
  src/vertexfilter.cpp
  src/vfetchanalyzer.cpp
  src/vfetchoptimizer.cpp
)
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/meshoptimizer/include)
list(APPEND defines _RELEASE)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines})
