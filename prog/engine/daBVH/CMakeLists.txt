# Software ray tracing BVHs: SAH BLAS building, quad/SoA4 leaf encodings, serialization, the TLAS and CPU traversal
set(includes ${CMAKE_CURRENT_SOURCE_DIR} shaders)
set(sources
  bvhBuild.cpp
  bvhIO.cpp
  bvhReencode.cpp
  bvhSerialization.cpp
  bvhTraversalQuadOOL.cpp
  quadBLASBuilder.cpp
  soa4Convert.cpp
  soa4EdgeFlags.cpp
  soa4TraversalOOL.cpp
  swTLAS.cpp
)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
