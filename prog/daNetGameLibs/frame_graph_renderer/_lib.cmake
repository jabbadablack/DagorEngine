if(DAGOR_GAME_RENDERER)
  dagor_game_lib(PULLS framework_frame_graph_renderer_pull daNetGameLibs_frame_graph_renderer_DAS_pull_AOT)
endif()
dagor_game_lib(INCLUDES ${DAGOR_PROG_DIR}/gameLibs/render/daFrameGraph DEPS daNetGameLibs/frame_graph_renderer)
