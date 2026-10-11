# Ported from prog/gameLibs/render/voxelizationTarget/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources voxelizationTarget.cpp)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  set(deps engine/baseUtil)
endif()
list(APPEND deps engine/lib3d)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
