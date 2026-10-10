# resUpd: updates game resource packs, vromfs packs and sound banks from new vromfs (gameResPatcher)
set(includes ${DAGOR_PROG_DIR}/gameLibs ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources resUpdate.cpp cmain.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/perfMon/daProfilerStub
  gameLibs/gameResPatcher
  tools/libTools/util
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(resUpd CONSOLE CDK EXCEPTIONS ON SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
