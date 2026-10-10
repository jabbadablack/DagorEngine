# Shader mesh resource building: shader and skin mesh data, LOD and UV checks, rendInst and dynmodel sources
set(sources
  shaderMeshData.cpp
  shSkinMeshData.cpp
  shaderMeshCacheOpt.cpp
  globalVertexDataConnector.cpp
  meshDataSave.cpp
  processMat.cpp
  validateLods.cpp
  validateUv.cpp
  validateAlphaTest.cpp
  dynSceneResSrc.cpp
  clothProxyBuild.cpp
  rendInstResSrc.cpp
  rendInstVoxel.cpp
  tristrip/stripobj.cpp
  tristrip/tristrip.cpp
  forsythTriangleReorderopt.cpp
)
set(includes
  ${DAGOR_PROG_DIR}/tools/sharedInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/tools/sceneTools/impostorBaker
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
set(deps 3rdPartyLibs/meshoptimizer 3rdPartyLibs/eastl gameLibs/render/omm)
if(DAGOR_ARCH STREQUAL "e2k")
  list(APPEND defines TEX_CANNOT_USE_ISPC)
else()
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/ispc_texcomp)
  list(APPEND deps 3rdPartyLibs/convert/ispc_texcomp)
endif()
list(APPEND defines _DEBUG_TAB_)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
