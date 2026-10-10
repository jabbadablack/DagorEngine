# HTTP streaming of files
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/ska_hash_map)
set(deps gameLibs/asyncHTTPClient 3rdPartyLibs/eastl)
set(sources http.cpp getdate.cpp)
list(APPEND defines CURL_STATICLIB)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
