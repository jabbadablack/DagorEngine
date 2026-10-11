# Ported from prog/gameLibs/render/rtr/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
if(DAGOR_GAME_BVH)
  set(sources rtr.cpp)
else()
  set(sources rtr_stub.cpp)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
