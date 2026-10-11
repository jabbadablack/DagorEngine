# Ported from prog/gameLibs/gpuMemoryInspector/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/imgui
  ${CMAKE_CURRENT_SOURCE_DIR}
)
set(sources gpuMemoryInspector.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
