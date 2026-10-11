# Ported from prog/gameLibs/levelSplines/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources levelSplines.cpp splineRegions.cpp splineRoads.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
