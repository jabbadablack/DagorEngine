# Ported from prog/gameLibs/nvCacheTracker/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/minhook/Include
)
set(sources nvCacheTracker.cpp)
set(deps 3rdPartyLibs/minhook gameLibs/statsd)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
