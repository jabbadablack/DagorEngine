# Ported from prog/gameLibs/perFrameStat/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources perFrameStat.cpp)
list(APPEND deps engine/workCycle gameLibs/render)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
