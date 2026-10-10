# csq, the console Quirrel interpreter of the CDK (with the game's script bindings: http, frp, json, jwt, yup files)
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/1stPartyLibs/quirrel/quirrel/squirrel
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs Shell32)
endif()
set(sources consoleSq.cpp scriptapi.cpp fs_utils.cpp con_main.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/coreUtil
  engine/math
  engine/consoleProc
  engine/perfMon/daProfilerStub
  engine/workCycle
  engine/lib3d
  engine/drv/drv3d_stub
  3rdPartyLibs/eastl
  3rdPartyLibs/libb64
  gameLibs/quirrel/bindQuirrelEx
  gameLibs/quirrel/quirrel_json
  gameLibs/quirrel/http
  gameLibs/quirrel/frp
  gameLibs/quirrel/sqJwt
  gameLibs/quirrel/base64
  gameLibs/quirrel/asyncRuntime
  gameLibs/asyncHTTPClient
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND deps gameLibs/quirrel/win_registry)
endif()
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub engine/workCycle/stub)
endif()
list(APPEND deps gameLibs/yup_parse gameLibs/quirrel/yupfile_parse)

dagor_add_executable(csq STRICT
  QUIRREL
  CONSOLE
  CDK
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
  PRIVATE_DEFINES HAS_YUP_PARSE
  SYSTEM_LIBS ${libs}
)
