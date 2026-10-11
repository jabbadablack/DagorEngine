# Ported from prog/gameLibs/effectManager/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/commonFx/commonFxGame)
if(DAGOR_GAME_RENDERER)
  list(APPEND sources effectManager.cpp)
else()
  list(APPEND sources stub/effectManagerStub.cpp)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
