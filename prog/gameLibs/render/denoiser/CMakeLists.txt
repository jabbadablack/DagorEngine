# The ray tracing denoiser (NRD), part of the BVH stack (DAGOR_GAME_BVH), or its stub. MathLib trips MSVC's C4587 in
# ml::float4x4, which warnings-as-errors make fatal: with MSVC, the stub.
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/math/sse2neon
  ${DAGOR_PROG_DIR}/3rdPartyLibs/math/MathLib
  ${DAGOR_PROG_DIR}/3rdPartyLibs/NRD
)
if(NOT DAGOR_GAME_BVH OR DAGOR_CC STREQUAL "msvc")
  dagor_add_library(STRICT SOURCES denoiser_stub.cpp PRIVATE_INCLUDES ${includes})
  return()
endif()
set(options)
if(DAGOR_PLATFORM STREQUAL "linux" AND DAGOR_SSE LESS 4)
  list(APPEND options -msse4) # one binary for the Linux clients: this lib is always SSE4
endif()
dagor_add_library(STRICT
  SOURCES denoiser.cpp
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES SSE2NEON_SUPPRESS_WARNINGS # sse2neon's advisory #warning is fatal as an error
  COMPILE_OPTIONS ${options}
)
