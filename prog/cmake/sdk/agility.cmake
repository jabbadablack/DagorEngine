# DirectX 12 Agility SDK (Windows): sdk::agility with its headers (before the Windows SDK's d3d12.h) and d3dx12.
# DAGOR_SDK_AGILITY_ROOT is the package's build/native; DAGOR_SDK_AGILITY_RUNTIME the DLLs a DX12 program ships with
# (D3D12Core and D3D12SDKLayers, in a D3D12 dir next to it).
set(DAGOR_SDK_AGILITY_ROOT "")
if(DAGOR_PLATFORM STREQUAL "windows")
  dagor_fetch_sdk(agility _dagor_agility_dir)
  set(DAGOR_SDK_AGILITY_ROOT "${_dagor_agility_dir}/build/native")
  add_library(sdk::agility INTERFACE IMPORTED GLOBAL)
  set_target_properties(sdk::agility PROPERTIES INTERFACE_INCLUDE_DIRECTORIES
    "${DAGOR_SDK_AGILITY_ROOT}/include;${DAGOR_SDK_AGILITY_ROOT}/include/d3dx12")
  if(DAGOR_ARCH STREQUAL "x86_64")
    set(_dagor_agility_bin "${DAGOR_SDK_AGILITY_ROOT}/bin/x64")
  else()
    set(_dagor_agility_bin "${DAGOR_SDK_AGILITY_ROOT}/bin/arm64")
  endif()
  set(DAGOR_SDK_AGILITY_RUNTIME "${_dagor_agility_bin}/D3D12Core.dll" "${_dagor_agility_bin}/d3d12SDKLayers.dll")
  unset(_dagor_agility_dir)
  unset(_dagor_agility_bin)
endif()
