# Code the 3d drivers share: GPU and display info, base textures, the resource checker, vendor integrations (NVAPI,
# AMD anti-lag and FSR, Streamline), hang handling
set(drivers ${DAGOR_D3D_DRIVERS})
set(sources
  drvDecl.cpp
  gpuMem.cpp
  gpuVendor.cpp
  gpuConfig.cpp
  display.cpp
  d3dToTexFmt.cpp
  basetexture.cpp
  drv_utils.cpp
  drv_resourceChecker.cpp
  dxgi_utils.cpp
  stereoHelper.cpp
  hangHandler.cpp
  ICrashFallback.cpp
  drv_returnAddrStore.cpp
  resUpdateBufferGeneric.cpp
  resourceActivationGeneric.cpp
  texResizeGeneric.cpp
  destroyEvent.cpp
  gpuLatency.cpp
)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/engine/drv/drv3d_commonCode)
set(defines)
set(source_options)
if(DAGOR_D3D_MULTI AND drivers STREQUAL "stub")
  list(APPEND defines D3D_STUB_DRIVER_ONLY)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources winapi_helpers.cpp)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources gpuMemM.mm macosx/macWnd.mm)
endif()
if(DAGOR_PLATFORM MATCHES "^(macOS|iOS|tvOS)$")
  list(APPEND sources displayM.mm)
endif()

dagor_require_sdk(nvapi OPTIONAL)
if(DAGOR_SDK_NVAPI_FOUND)
  list(APPEND sources nvLowLatency.cpp)
  list(APPEND deps sdk::nvapi)
else()
  list(APPEND sources nvLowLatencyStub.cpp)
endif()

set(real_drivers ${drivers})
list(REMOVE_ITEM real_drivers stub null)
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64" AND real_drivers)
  list(APPEND sources amdLowLatency.cpp)
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/AntiLag2)
else()
  list(APPEND sources amdLowLatencyStub.cpp)
endif()
if(DAGOR_STREAMLINE)
  dagor_require_sdk(streamline)
  list(APPEND sources streamline_adapter.cpp)
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include)
  list(APPEND defines HAS_STREAMLINE)
  list(APPEND deps sdk::streamline)
else()
  list(APPEND sources streamline_adapter_stub.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64")
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/adl_sdk/include ${DAGOR_PROG_DIR}/3rdPartyLibs/AmdDxExt)
  list(APPEND defines HAS_ADL HAS_AMD_DX_EXT)
endif()
if(DAGOR_PLATFORM MATCHES "^(windows|linux)$" AND real_drivers AND NOT DAGOR_DEDICATED)
  list(APPEND sources amdFsr.cpp)
  if("vulkan" IN_LIST drivers AND DAGOR_ARCH STREQUAL "x86_64")
    list(APPEND source_options amdFsr.cpp -DAMDFSR_HAS_VULKAN)
  endif()
  if("DX12" IN_LIST drivers AND DAGOR_ARCH STREQUAL "x86_64")
    list(APPEND source_options amdFsr.cpp -DAMDFSR_HAS_DX12)
  endif()
else()
  list(APPEND sources amdFsr_stub.cpp)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  SOURCE_OPTIONS ${source_options}
  DEPS engine/drv/shadersMetaData
)
