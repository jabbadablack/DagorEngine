# Ported from prog/gameLibs/projectiveDecals/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources
  defaultDecalData.cpp
  projectiveDecals.cpp
  projectiveDecalsBuffer.cpp
  resizableProjectiveDecals.cpp
  ringBufferProjectiveDecals.cpp
)
list(APPEND deps engine/lib3d gameLibs/render)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
