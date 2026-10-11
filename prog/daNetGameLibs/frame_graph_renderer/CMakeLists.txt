set(das)
if(DAGOR_GAME_RENDERER)
  set(das render)
endif()
dagor_add_dng_module(frame_graph_renderer DAS DAS_DIRS ${das}
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/gameLibs/render/daFrameGraph
    ${DAGOR_PROG_DIR}/daNetGame
    ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
)
