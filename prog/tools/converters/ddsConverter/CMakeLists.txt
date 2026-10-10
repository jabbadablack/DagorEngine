# ddsConverter: converts images to DDS textures
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources ddsConverter.cpp con_main.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/image
  engine/drv/drv3d_null
  engine/perfMon/daProfilerStub
  tools/libTools/util
  tools/libTools/dtx
  3rdPartyLibs/image/psdRead
  3rdPartyLibs/image/libpng-1.4.22
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(ddsConverter CONSOLE CDK SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
