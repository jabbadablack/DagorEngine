# JSON RPC over persistent websocket connections
list(APPEND includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
)
list(APPEND deps engine/crypto gameLibs/websocket 3rdPartyLibs/arc/zstd-1.4.5)
set(AllSrcFolder_CPP .)
dagor_glob_sources(sources DIRS ${AllSrcFolder_CPP} GLOB *.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /FC)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options} DEPS ${deps})
