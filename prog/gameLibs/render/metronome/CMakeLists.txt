# Metronome: frame pacing measurements on top of daFrameGraph
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources metronome.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
