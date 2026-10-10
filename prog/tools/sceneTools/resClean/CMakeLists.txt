# resCleanUtil: finds (and with -clean removes) GRP/DxP files not in the resource pack list of a vromfs
set(sources resCleanUtil.cpp)
set(includes ${DAGOR_PROG_DIR}/engine ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/perfMon/daProfilerStub
  tools/libTools/util
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(resCleanUtil CONSOLE CDK SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
