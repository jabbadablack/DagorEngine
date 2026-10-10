# The vromfs pack builder: file selection by patterns, BLK and text preprocessing, packing
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/tools/sharedInclude)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
list(APPEND deps 3rdPartyLibs/openssl-3.x)
set(sources vromfsPacker.cpp processFile.cpp)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps engine/osApiWrappers engine/ioSys engine/baseUtil)
endif()
list(APPEND deps tools/libTools/util 3rdPartyLibs/hash/BLAKE3)
if(DAGOR_PLATFORM STREQUAL "macOS" OR DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND options -Wno-deprecated-declarations)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options} DEPS ${deps})
