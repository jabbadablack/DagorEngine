# Debug drawing of solid shapes (meshes, spheres, capsules, cubes, cones), immediate and buffered with a lifetime
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources debug3dSolid.cpp debug3dSolidBuffered.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
