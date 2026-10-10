# Decoding of the SPIR-V shader metadata: chunked containers and SMOL-V decompression
set(sources unpack.cpp)
list(APPEND includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/smol-v/source
)
list(APPEND deps 3rdPartyLibs/vulkan/smol-v)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
