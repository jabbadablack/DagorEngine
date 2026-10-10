# OpenSSL 3: libssl and the default provider, on libcrypto (crypto/), with zlib compression
include(openssl.cmake)

set(sources)
openssl_collect_c(sources providers/common securitycheck_fips.c)
foreach(dir providers/common/der providers/implementations/asymciphers providers/implementations/digests
            providers/implementations/encode_decode providers/implementations/exchange providers/implementations/kdfs
            providers/implementations/kem providers/implementations/keymgmt providers/implementations/rands
            providers/implementations/signature providers/implementations/storemgmt ssl ssl/record ssl/statem)
  openssl_collect_c(sources ${dir})
endforeach()
openssl_collect_c(sources providers/implementations/ciphers cipher_rc4_hmac_md5_hw.c)
openssl_collect_c(sources providers/implementations/macs blake2_mac_impl.c)
list(APPEND sources providers/baseprov.c providers/defltprov.c providers/nullprov.c providers/prov_running.c
  gaijin_stubs/getenv.c)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources providers/implementations/rands/seeding/rand_win.c)
else()
  list(APPEND sources providers/implementations/rands/seeding/rand_unix.c)
endif()

set(c_options ${OPENSSL_C_OPTIONS})
if(DAGOR_CC MATCHES "^(clang|clang-cl)$" AND DAGOR_SANITIZE STREQUAL "undefined")
  list(APPEND c_options -fno-sanitize=undefined)
elseif(DAGOR_CC STREQUAL "gcc" AND DAGOR_SANITIZE STREQUAL "thread")
  list(APPEND c_options -fno-sanitize=thread)
endif()
set(source_options)
set(libs)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(libs Ws2_32 Advapi32)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  set(source_options ssl/ssl_lib.c -Wno-deprecated-declarations)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES ${OPENSSL_INCLUDES}
  PRIVATE_DEFINES ${OPENSSL_C_DEFINES} ZLIB
  C_OPTIONS ${c_options}
  SOURCE_OPTIONS ${source_options}
  DEPS 3rdPartyLibs/openssl-3.x/crypto 3rdPartyLibs/arc/zlib-ng
  SYSTEM_LIBS ${libs}
  LICENSE_FILES LICENSE.txt
)
