# Streams (files, memory, zlib, zstd, lzma, brotli, Oodle), async I/O, vromfs, findFiles. Oodle is not redistributable:
# with -DDAGOR_SDK_OODLE_DIR=<oodle SDK> its codecs are built in, otherwise a stub reports them unsupported.
set(sources
  baseIo.cpp
  fileIo.cpp
  memIo.cpp
  chainedMemIo.cpp
  ioUtils.cpp
  zlibIo.cpp
  zlibIoFatal.cpp
  zstdIo.cpp
  zstdIoFatal.cpp
  asyncIo.cpp
  asyncIoCached.cpp
  msgIo.cpp
  obsolete_cfg.cpp
  roDataBlk.cpp
  vromfsLoad.cpp
  vromfsBacked.cpp
  findFiles.cpp
  fastSeqRead.cpp
  asyncWrite.cpp
  lzmaDecIo.cpp
  lzmaEnc.cpp
  lzmaIoFatal.cpp
  brotli.cpp
)
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/brotli/include
)
set(deps
  engine/ioSys/dataBlock
  3rdPartyLibs/hash
  3rdPartyLibs/arc/zlib-ng
  3rdPartyLibs/arc/zstd-1.4.5
  3rdPartyLibs/arc/lzma-9.20
  3rdPartyLibs/arc/brotli
)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps 3rdPartyLibs/eastl)
endif()

dagor_require_sdk(oodle OPTIONAL)
if(DAGOR_SDK_OODLE_FOUND)
  list(APPEND sources oodleIo.cpp oodleIoFatal.cpp)
  list(APPEND includes ${DAGOR_SDK_OODLE_ROOT}/include)
  list(APPEND deps sdk::oodle)
else()
  list(APPEND sources oodleIoStub.cpp)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES __B_KERNEL_LIB USE_ZLIB_VER=0xFF0000
  DEPS ${deps}
)
