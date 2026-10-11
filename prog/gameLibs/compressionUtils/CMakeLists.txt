# The compression of vromfs and network data: zlib and zstd. The full set (lz4, snappy, bzip2) needs
# 3rdPartyLibs/arc/snappy-1.1.9 and bzip2-1.0.3, which the fork has not, so this is the minimum set jam built without
# them (DAGOR_MINIMUM_COMPR_UTILS). jamfile-utils (the bsdiff tools) is not ported.
dagor_add_library(
  SOURCES
    compression.cpp
    vromfsCompressionImpl.cpp
    memSilentInPlaceLoadCB.cpp
    bsdiffwrap.cpp
    bulkBlkPack.cpp
    blobMultiStorage.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude/compressionUtils
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/tools/sharedInclude
    ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
    ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
    ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include
  PRIVATE_DEFINES DAGOR_MINIMUM_COMPR_UTILS OPENSSL_SUPPRESS_DEPRECATED
  DEPS 3rdPartyLibs/arc/zlib-ng 3rdPartyLibs/arc/zstd-1.4.5 3rdPartyLibs/bsdiff
)
