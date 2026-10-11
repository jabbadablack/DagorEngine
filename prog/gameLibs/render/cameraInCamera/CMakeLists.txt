# Ported from prog/gameLibs/render/cameraInCamera/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(AllSrcFolder_CPP )
set(AllSrcFolder_ES )
if(DAGOR_GAME_RENDERER)
  list(APPEND AllSrcFolder_ES render)
  list(APPEND AllSrcFolder_CPP render)
endif()

dagor_add_dng_module(cameraInCamera CPP_DIRS ${AllSrcFolder_CPP}
  ES_DIRS ${AllSrcFolder_ES}
  PRIVATE_INCLUDES ${includes}
)
