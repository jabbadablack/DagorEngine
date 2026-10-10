# daNet: the ENet based network transport
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng ${DAGOR_PROG_DIR}/3rdPartyLibs/enet/include)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
set(deps 3rdPartyLibs/arc/zlib-ng 3rdPartyLibs/enet)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/posix/include/win32)
  list(APPEND deps 3rdPartyLibs/posix)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
