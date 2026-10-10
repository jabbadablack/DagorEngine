# Asynchronous HTTP client on libcurl
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND deps 3rdPartyLibs/eastl)
set(sources curl.cpp curl_global.cpp)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/libcurl/include)
list(APPEND deps 3rdPartyLibs/libcurl)
list(APPEND defines CURL_STATICLIB)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
