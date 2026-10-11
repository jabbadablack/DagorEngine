# Ported from prog/gameLibs/frameTimeMetrics/jamfile (jam2cmake/skeleton.py)
set(sources aggregator.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
