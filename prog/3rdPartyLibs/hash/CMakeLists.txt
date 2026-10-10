# sha1/sha256/sha3/md5/xxhash/crc32/rijndael; the SHA-2 implementation comes from OpenSSL's sha module
set(sources
  sha1.cpp
  sha256.cpp
  sha3.cpp
  md5.c
  xxhash.c
  crc32.c
  crc32c.c
  rijndael-alg-fst.c
  rijndael-api-fst.c
  xxh_x86dispatch_auto.c
  SHA3IUF/sha3.c
)
set(c_options)
set(source_options)
if(DAGOR_CC STREQUAL "msvc")
  # warning 6386: Buffer overrun: accessing 'argument 1', the writable size is '64' bytes, but '746' bytes might be written
  list(APPEND c_options /wd6386)
elseif(DAGOR_CC STREQUAL "clang-cl" AND DAGOR_ARCH STREQUAL "x86_64")
  list(APPEND source_options crc32c.c -mcrc32)
endif()
set(options)
if(DAGOR_ARCH STREQUAL "e2k")
  list(APPEND options -Wno-reduced-alignment)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES . SHA3IUF ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include
  PRIVATE_DEFINES OPENSSL_SUPPRESS_DEPRECATED
  COMPILE_OPTIONS ${options}
  C_OPTIONS ${c_options}
  SOURCE_OPTIONS ${source_options}
  DEPS 3rdPartyLibs/openssl-3.x/crypto/sha
)
