# The tools asset manager: asset bases and types, assets from game resources and DDSx textures, change tracking
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources
  assetMgr.cpp
  assetFromGameRes.cpp
  assetFromDdsxTex.cpp
  assetFromGameResEx.cpp
  asset.cpp
  vAssetRule.cpp
  assetMsgPipe.cpp
  assetMgrTrackChanges.cpp
  assetFind.cpp
  daBuildDLL.cpp
)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
