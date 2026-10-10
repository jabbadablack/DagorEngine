# Graph layout for node graph visualizations
set(sources defaultGraphLayouter.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
