# Ported from prog/gameLibs/hudprim/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources hudPrimitives.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
