# Ported from prog/gameLibs/gpuMemoryDumper/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources gpuMemoryDumper.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
