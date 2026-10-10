# vromfsPacker: the virtual ROM file system (vromfs) pack builder (gameLibs/vromfsPacker)
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources cmain.cpp)
set(deps
  engine/kernel
  engine/memory
  engine/perfMon/daProfilerStub
  engine/startup
  engine/math
  gameLibs/vromfsPacker
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs advapi32)
endif()
if(DAGOR_PLATFORM STREQUAL "linux")
  set(libs dl)
endif()
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(vromfsPacker CONSOLE
  CDK
  EXCEPTIONS ON
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
