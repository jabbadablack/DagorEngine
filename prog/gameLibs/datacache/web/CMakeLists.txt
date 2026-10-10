# Data cache: the web (HTTP) backend
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(deps 3rdPartyLibs/eastl gameLibs/datacache/common gameLibs/datacache/file gameLibs/streamIO)
set(sources webbackend.cpp webindex.cpp webutil.cpp gzip.cpp)
list(APPEND defines OPENSSL_SUPPRESS_DEPRECATED)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
list(APPEND deps 3rdPartyLibs/openssl-3.x)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
