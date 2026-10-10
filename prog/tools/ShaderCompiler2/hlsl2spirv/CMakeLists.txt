# The Vulkan back end of the shader compilers: HLSL to SPIR-V through DXC, optimized with spirv-tools and packed with
# smol-v
dagor_require_sdk(dxc)
set(libs)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(libs d3dcompiler)
endif()
dagor_add_library(
  SOURCES asmShaderSpirV.cpp HLSL2SpirvCommon.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/smol-v/source
    ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/spirv-tools/include
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  PRIVATE_DEFINES _CROSS_TARGET_SPIRV BINDUMP_TARGET_BE=0 _CRT_SECURE_NO_DEPRECATE _HAS_EXCEPTIONS=0 _SECURE_SCL=0
    EXCLUDE_PSTDINT
  DEPS 3rdPartyLibs/hash 3rdPartyLibs/vulkan/smol-v 3rdPartyLibs/vulkan/spirv-tools 3rdPartyLibs/eastl gameLibs/spirv
    sdk::dxc
  SYSTEM_LIBS ${libs}
)
