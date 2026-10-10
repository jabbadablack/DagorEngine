# Debug mesh coloring modes (the debug gbuffer modes, overdraw) and their console command
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources debugMesh.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
