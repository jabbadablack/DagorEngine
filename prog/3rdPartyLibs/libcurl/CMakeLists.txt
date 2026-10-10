# libcurl (HTTP only) on the vendored OpenSSL, zlib-ng, zstd and brotli
set(includes
  lib
  include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/brotli/include
)
list(APPEND deps 3rdPartyLibs/arc/zlib-ng 3rdPartyLibs/arc/zstd-1.4.5 3rdPartyLibs/arc/brotli)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs Ws2_32 crypt32)
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND options -Wno-deprecated-declarations)
  list(APPEND libs -Wl,-framework,SystemConfiguration)
endif()
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
list(APPEND deps 3rdPartyLibs/openssl-3.x)
dagor_glob_sources(sources DIRS lib/vauth lib GLOB *.c)
list(APPEND sources
  lib/vtls/openssl.c
  lib/vtls/keylog.c
  lib/vtls/hostcheck.c
  lib/vtls/x509asn1.c
  lib/vtls/vtls.c
)
set(c_options
  -DOPENSSL_SUPPRESS_DEPRECATED
  -DCURL_STATICLIB
  -DBUILDING_LIBCURL
  -DCURL_DISABLE_LDAP
  -DHTTP_ONLY
  -DHAVE_BROTLI
  -DHAVE_ZSTD
  -DHAVE_LIBZ
  -DHAVE_ZLIB_H
)
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  if(DAGOR_SANITIZE STREQUAL "undefined")
    list(APPEND c_options -fno-sanitize=undefined)
  endif()
  list(APPEND c_options -Wno-incompatible-pointer-types-discards-qualifiers)
endif()
if(DAGOR_CC STREQUAL "gcc")
  list(APPEND c_options -Wno-discarded-qualifiers)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|iOS|linux|macOS|tvOS)$")
  list(APPEND defines HAVE_CONFIG_H)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  C_OPTIONS ${c_options}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
