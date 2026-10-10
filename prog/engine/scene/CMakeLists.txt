# Static scenes: tiled scenes, visibility trees, occlusion maps, level loading, ray tracer dumps, physical materials
set(sources
  scene.cpp
  sceneIo.cpp
  tiledScene.cpp
  buildVisTree.cpp
  loadLevel.cpp
  physMat.cpp
  frtdump.cpp
  frtdumpMgr.cpp
  renderSceneMgr.cpp
  staticFxObjs.cpp
  visibility.cpp
  occlusionMap.cpp
  objsToPlace.cpp
  kdtree.cpp
  occlusionIo.cpp
)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
list(APPEND deps 3rdPartyLibs/eastl)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
