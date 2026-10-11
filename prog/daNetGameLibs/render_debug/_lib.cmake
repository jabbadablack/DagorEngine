dagor_game_lib(PULLS framework_render_debug_pull DEPS daNetGameLibs/render_debug)
# the das sources all live under render/: on a renderless build there is no AOT pull to reference
if(DAGOR_GAME_RENDERER)
  dagor_game_lib(PULLS daNetGameLibs_render_debug_DAS_pull_AOT)
endif()
