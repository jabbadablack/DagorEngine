# resDiffUtil: builds patches of game resource packs (GRP/DxP) between a base and a new game root
set(sources resDiffUtil.cpp cmain.cpp)
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/engine
  ${DAGOR_PROG_DIR}/tools/sharedInclude
)
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

dagor_add_executable(resDiffUtil CONSOLE CDK SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
