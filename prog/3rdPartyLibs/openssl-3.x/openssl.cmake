# Settings shared by the OpenSSL 3 libraries (openssl-3.x and its crypto/sha module), from jam's ssl-options.jam:
# OPENSSL_DIR, OPENSSL_INCLUDES, OPENSSL_C_DEFINES, OPENSSL_C_OPTIONS, OPENSSL_ASM (whether the perlasm sources are
# used) and OPENSSL_ASM_EXT (.asm NASM on Windows, .s GAS elsewhere).
set(OPENSSL_DIR "${CMAKE_CURRENT_LIST_DIR}")
set(OPENSSL_INCLUDES
  ${OPENSSL_DIR}/include
  ${OPENSSL_DIR}
  ${OPENSSL_DIR}/crypto/include
  ${OPENSSL_DIR}/crypto/modes
  ${OPENSSL_DIR}/providers/implementations/include
  ${OPENSSL_DIR}/providers/common/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
)

set(OPENSSL_ASM ON)
if(DAGOR_PLATFORM MATCHES "^(android|macOS|tvOS|iOS)$" OR DAGOR_ARCH MATCHES "^(e2k|arm64)$")
  set(OPENSSL_ASM OFF)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  set(OPENSSL_ASM_EXT asm)
else()
  set(OPENSSL_ASM_EXT s)
endif()

set(OPENSSL_C_DEFINES MODULESDIR="" OPENSSLDIR="" ENGINESDIR="" OPENSSL_NO_UI_CONSOLE DSO_NONE OPENSSL_NO_INLINE_ASM
  OPENSSL_NO_KTLS OPENSSL_NO_ENGINE)
if(OPENSSL_ASM)
  list(APPEND OPENSSL_C_DEFINES OPENSSL_CPUID_OBJ OPENSSL_BN_ASM_MONT SHA1_ASM SHA256_ASM SHA512_ASM RC4_ASM MD5_ASM
    AES_ASM GHASH_ASM KECCAK1600_ASM)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|iOS|tvOS)$")
  list(APPEND OPENSSL_C_DEFINES OPENSSL_NO_ASYNC)
endif()
set(OPENSSL_C_OPTIONS)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND OPENSSL_C_DEFINES NDEBUG OPENSSL_SYS_WIN32 OPENSSL_NO_EC_NISTP_64_GCC_128 UNICODE _UNICODE)
  set(OPENSSL_C_OPTIONS -wd4090 -wd4133)
endif()

# the C sources of <dir> (relative to the OpenSSL root) except the named files
function(openssl_collect_c out dir)
  file(GLOB found "${OPENSSL_DIR}/${dir}/*.c")
  foreach(name IN LISTS ARGN)
    list(FILTER found EXCLUDE REGEX "/${name}$")
  endforeach()
  list(SORT found)
  set(${out} ${${out}} ${found} PARENT_SCOPE)
endfunction()

# the perlasm sources of <dir>
function(openssl_collect_asm out dir)
  file(GLOB found "${OPENSSL_DIR}/${dir}/*.${OPENSSL_ASM_EXT}")
  list(SORT found)
  set(${out} ${${out}} ${found} PARENT_SCOPE)
endfunction()
