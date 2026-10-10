# Primitive mesh generation for rendering: spheres, cylinders and cube indices
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources primitiveObjects.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
