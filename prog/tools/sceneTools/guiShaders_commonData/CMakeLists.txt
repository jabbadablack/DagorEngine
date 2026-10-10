# The minimal GUI shaders of the engine tools (the default GUI and ImGui), for each API the host's tools render with:
# guiShaders (DX11), guiShadersDX12 and guiShadersSpirV on Windows, guiShadersSpirV on Linux, guiShadersMTL on macOS.
# They go into <build>/commonData and, with the cdk-data install component, into tools/dagor_cdk/commonData.
dagor_use(tools/ShaderCompiler2)
set(out "${CMAKE_BINARY_DIR}/commonData")
set(dest tools/dagor_cdk/commonData)
if(DAGOR_PLATFORM STREQUAL "windows")
  dagor_add_shaders(guiShaders-dx11 COMPILER dsc2-hlsl11 BLK shaders_guiMinimal.blk OUTPUT "${out}/guiShaders"
    INSTALL ${dest} COMPONENT cdk-data)
  dagor_add_shaders(guiShaders-dx12 COMPILER dsc2-dx12 BLK shaders_guiMinimal.blk OUTPUT "${out}/guiShadersDX12"
    ARGS -maxVSF 4096 INSTALL ${dest} COMPONENT cdk-data)
endif()
if(DAGOR_PLATFORM MATCHES "^(windows|linux)$")
  dagor_add_shaders(guiShaders-spirv COMPILER dsc2-spirv BLK shaders_guiMinimal.blk OUTPUT "${out}/guiShadersSpirV"
    INSTALL ${dest} COMPONENT cdk-data)
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  dagor_add_shaders(guiShaders-metal COMPILER dsc2-metal BLK shaders_guiMinimal.blk OUTPUT "${out}/guiShadersMTL"
    INSTALL ${dest} COMPONENT cdk-data)
endif()
