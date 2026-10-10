# OpenSSL's SHA-1/2/3 alone (with the CPU detection it needs), for the libraries that hash without the rest of OpenSSL
include(../../openssl.cmake)

set(sources ${OPENSSL_DIR}/crypto/cryptlib.c ${OPENSSL_DIR}/crypto/cpuid.c ${OPENSSL_DIR}/crypto/ctype.c)
openssl_collect_c(sources crypto/sha keccak1600.c)
if(OPENSSL_ASM)
  openssl_collect_asm(sources crypto/sha)
  list(APPEND sources ${OPENSSL_DIR}/crypto/x86_64cpuid.${OPENSSL_ASM_EXT})
else()
  list(APPEND sources ${OPENSSL_DIR}/crypto/mem_clr.c ${OPENSSL_DIR}/crypto/sha/keccak1600.c)
endif()
set(libs)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(libs Ws2_32 Advapi32)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES ${OPENSSL_INCLUDES}
  PRIVATE_DEFINES ${OPENSSL_C_DEFINES}
  C_OPTIONS ${OPENSSL_C_OPTIONS}
  SYSTEM_LIBS ${libs}
  LICENSE_FILES ${OPENSSL_DIR}/LICENSE.txt
)
