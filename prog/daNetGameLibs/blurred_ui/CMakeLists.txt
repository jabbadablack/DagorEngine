set(es)
if(DAGOR_GAME_RENDERER)
  set(es render)
endif()
dagor_add_dng_module(blurred_ui ES_DIRS ${es}
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/daNetGameLibs
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/daNetGame
)
