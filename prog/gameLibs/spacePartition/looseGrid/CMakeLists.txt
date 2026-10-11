# Ported from prog/gameLibs/spacePartition/looseGrid/jamfile (jam2cmake/skeleton.py)
set(sources looseGrid.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
