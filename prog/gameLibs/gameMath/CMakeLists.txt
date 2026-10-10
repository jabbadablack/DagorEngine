# Game math helpers: convex construction and segments, interpolation tables from BLK, collision node distances
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/)
set(sources constructConvex.cpp convexUtils.cpp interpolateTabUtils.cpp mathUtils.cpp collResUtils.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
