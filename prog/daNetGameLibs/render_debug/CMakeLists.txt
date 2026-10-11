set(dirs)
if(DAGOR_GAME_RENDERER)
  set(dirs render)
  dagor_game_lib(PULLS debug_indoor_probe_boxes_console_handler_pull gpu_driven_debug_renderer_pull)
endif()
dagor_add_dng_module(render_debug CPP_DIRS ${dirs} ES_DIRS ${dirs} DAS DAS_DIRS ${dirs}
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/daNetGame
    ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
    ${DAGOR_PROG_DIR}/1stPartyLibs/rapidJsonUtils/include
)
