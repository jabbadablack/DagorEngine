# Ported from prog/gameLibs/daProfilerPlugins/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources daProfilerVSync.cpp)
list(APPEND deps engine/perfMon)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
