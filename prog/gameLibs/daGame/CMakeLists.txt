# Ported from prog/gameLibs/daGame/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources netUnit.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
