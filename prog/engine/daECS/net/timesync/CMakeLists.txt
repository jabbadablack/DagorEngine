# Ported from prog/engine/daECS/net/timesync/jamfile (jam2cmake/skeleton.py)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})

dagor_add_library(STRICT SOURCES ${sources})
