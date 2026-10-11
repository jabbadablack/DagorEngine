# Ported from prog/gameLibs/daSkies2/debug/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources cloudsFieldDebug.cpp)
list(APPEND deps gameLibs/render/daFrameGraph)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
