# Websocket JSON RPC unit tests
set(AllSrcFolder_CPP . wsJsonRpcConnection wsJsonRpcPersistentConnection)
dagor_glob_sources(sources DIRS ${AllSrcFolder_CPP} GLOB *.cpp)
list(APPEND includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/websocketJsonRpc/tests
)
list(APPEND defines USE_EASTL)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /FC)
endif()
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/perfMon/daProfilerStub
  3rdPartyLibs/eastl
  gameLibs/websocketJsonRpc
  gameLibs/websocketJsonRpc/tests/testHelpers
)

dagor_add_catch2_test(websocketJsonRpc-tests TAGS gameLibs net
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
