# Websocket client on libcurl
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/libb64/include)
list(APPEND deps 3rdPartyLibs/eastl 3rdPartyLibs/libb64 3rdPartyLibs/hash engine/crypto)
set(sources websocket.cpp)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/libcurl/include)
list(APPEND deps 3rdPartyLibs/libcurl)
list(APPEND defines CURL_STATICLIB)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /FC)
endif()
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
list(APPEND deps 3rdPartyLibs/openssl-3.x)

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
