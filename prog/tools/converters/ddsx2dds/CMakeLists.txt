# ddsx2dds: converts DDSx textures back to DDS (PC formats) and dumps their headers
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(sources ddsx2dds.cpp)
set(deps
  engine/osApiWrappers
  engine/osApiWrappers/messageBox/stub
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/perfMon/daProfilerStub
)

dagor_add_executable(ddsx2dds CONSOLE
  CDK
  NO_CONFIG_POSTFIX
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
)
