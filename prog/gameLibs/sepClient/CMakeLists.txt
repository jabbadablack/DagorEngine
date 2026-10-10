# SEP client: JSON RPC over websockets with hostname resolution through c-ares
list(APPEND includes
  ${DAGOR_PROG_DIR}/dagorInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
)
list(APPEND deps gameLibs/websocketJsonRpc)
set(AllSrcFolder_CPP .)
dagor_glob_sources(sources DIRS ${AllSrcFolder_CPP} GLOB *.cpp)
list(APPEND deps 3rdPartyLibs/c-ares)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/c-ares)
list(APPEND defines SEPCLIENT_USE_CARES CARES_STATICLIB)
list(APPEND sources asyncHostnameResolver/asyncHostnameResolverCAres.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /FC)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
