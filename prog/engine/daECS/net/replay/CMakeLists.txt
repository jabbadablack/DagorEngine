# Ported from prog/engine/daECS/net/replay/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include)
set(sources replay.cpp stubs.cpp)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps engine/ioSys)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
