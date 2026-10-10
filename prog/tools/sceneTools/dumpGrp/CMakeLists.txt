# dumpGrp: dumps game resource packs (grp), texture packs and level binaries, with the textures they reference
set(includes
  ${DAGOR_PROG_DIR}/tools/sharedInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/engine
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
set(sources dumpGrp.cpp dumpGrpTexRef.cpp cmain.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  tools/libTools/util
  engine/drv/drv3d_stub
  engine/perfMon
  engine/gameRes
  engine/lib3d
  engine/libFx
  commonFx/commonFxGame
  engine/shaders
  engine/scene
  engine/coreUtil
  engine/shaders
  engine/sceneRay
  gameLibs/rendInst
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox)
endif()

dagor_add_executable(dumpGrp CONSOLE CDK SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
