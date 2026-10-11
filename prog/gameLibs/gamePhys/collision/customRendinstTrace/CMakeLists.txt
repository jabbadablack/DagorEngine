# Ported from prog/gameLibs/gamePhys/collision/customRendinstTrace/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources customRendinstTrace.cpp)
list(APPEND deps gameLibs/landMesh)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
