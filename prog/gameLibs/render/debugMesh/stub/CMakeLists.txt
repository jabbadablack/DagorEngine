# Debug mesh coloring stubs for programs without it
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources debugMesh.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
