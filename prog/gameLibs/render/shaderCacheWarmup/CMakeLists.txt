# Ported from prog/gameLibs/render/shaderCacheWarmup/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${CMAKE_CURRENT_SOURCE_DIR}
)
set(sources shaderCacheWarmup.cpp startup.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
