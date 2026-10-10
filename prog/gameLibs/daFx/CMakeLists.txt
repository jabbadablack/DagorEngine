# daFx: the particle effects runtime (systems, emitters, instances, GPU buffers, culling and rendering)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources
  binds.cpp
  render.cpp
  systems.cpp
  shaders.cpp
  buffers.cpp
  culling.cpp
  context.cpp
  emitters.cpp
  instances.cpp
  globalData.cpp
  frameBoundaryBufferManager.cpp
)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
