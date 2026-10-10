# ddsxCvt: converts DDS textures to the DDSx of a target platform through the DDSx plugins
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources ddsxConverter.cpp con_main.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/perfMon/daProfilerStub
  tools/libTools/dtx
  tools/libTools/util
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(ddsxCvt CONSOLE
  CDK
  NO_CONFIG_POSTFIX
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
)
