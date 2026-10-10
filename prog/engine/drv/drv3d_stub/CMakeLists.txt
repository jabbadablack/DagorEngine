# The stub 3d driver: the whole driver interface without a GPU (tools, servers, the render tests without a GPU)
set(options)
if(DAGOR_MSVC_LIKE)
  set(options /FId3d_config.h)
else()
  set(options "SHELL:-include ${CMAKE_CURRENT_SOURCE_DIR}/d3d_config.h")
endif()
dagor_add_library(STRICT
  SOURCES d3d_stub.cpp init_d3di.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/engine/drv/drv3d_commonCode
    .
  PRIVATE_DEFINES D3DSTUBBED INSIDE_DRIVER
  COMPILE_OPTIONS ${options}
  DEPS engine/drv/drv3d_commonCode
)
