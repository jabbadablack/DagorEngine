# Ported from prog/gameLibs/grid/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources spatialHashGrid.cpp)
list(APPEND deps gameLibs/gameMath)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
