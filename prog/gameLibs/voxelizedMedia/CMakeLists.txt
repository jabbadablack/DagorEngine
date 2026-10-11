# Ported from prog/gameLibs/voxelizedMedia/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR} shaders)
set(deps engine/lib3d)
set(AllSrcFolder_CPP .)

dagor_add_dng_module(voxelizedMedia CPP_DIRS ${AllSrcFolder_CPP} PRIVATE_INCLUDES ${includes} DEPS ${deps})
