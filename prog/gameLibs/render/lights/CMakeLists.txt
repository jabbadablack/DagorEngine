# Dynamic lights: omni and spot light managers, clustered and tiled light culling, light shadows
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${DAGOR_PROG_DIR}/gameLibs/render/shaders
  ${DAGOR_PROG_DIR}/3rdPartyLibs/binPack2D/include
)
set(sources
  clusteredLights.cpp
  clusteredLightsGrid.cpp
  lightsSorter.cpp
  lightsPartition.cpp
  lightsManager.cpp
  omniLightsManager.cpp
  spotLightsManager.cpp
  tiledLights.cpp
  frustumClusters.cpp
  shadowSystem.cpp
  reallocatableLightsConstBuffer.cpp
  lightsResources.cpp
  dstReadbackLights.cpp
  lightsRenderer.cpp
  dynamicLightShadows.cpp
  lightsVisibilityChecker.cpp
)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
