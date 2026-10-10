# The DX12 back end of the shader compilers: HLSL to DXIL through DXC (with FXC still the preprocessor, as DXC follows
# the proper C preprocessor rules and not MS's ones)
dagor_require_sdk(dxc)
dagor_add_library(
  SOURCES asmShaderDXIL.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators/mimalloc/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators/mimalloc/mimalloc/include
  PRIVATE_DEFINES _CROSS_TARGET_DX12 _CROSS_TARGET_DX12_DXIL BINDUMP_TARGET_BE=0 _CRT_SECURE_NO_DEPRECATE
    _HAS_EXCEPTIONS=0 _SECURE_SCL=0 EXCLUDE_PSTDINT
  DEPS 3rdPartyLibs/hash 3rdPartyLibs/memAllocators/mimalloc:nodebug gameLibs/dxil sdk::dxc
  SYSTEM_LIBS d3dcompiler
)
