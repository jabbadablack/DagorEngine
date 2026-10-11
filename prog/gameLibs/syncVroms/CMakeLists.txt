# the vroms' hashes: BLAKE3, shortened (vromHash_sha1.cpp is the other algorithm, which no game uses)
dagor_add_library(STRICT
  SOURCES vromHash.cpp syncVroms.cpp vromHash_blake3short.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  DEPS gameLibs/compressionUtils 3rdPartyLibs/hash 3rdPartyLibs/hash/BLAKE3
)
