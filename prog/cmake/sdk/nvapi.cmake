# NVIDIA NVAPI (Windows): sdk::nvapi with the headers and the library of the target arch. Sets DAGOR_SDK_NVAPI_ROOT,
# empty when the SDK has no library for the arch (as for arm64 in R610): the users then build without HAS_NVAPI.
set(DAGOR_SDK_NVAPI_ROOT "")
if(DAGOR_PLATFORM STREQUAL "windows")
  dagor_fetch_sdk(nvapi _dagor_nvapi_dir)
  if(DAGOR_ARCH STREQUAL "x86_64")
    set(_dagor_nvapi_lib "${_dagor_nvapi_dir}/amd64/nvapi64.lib")
  else()
    set(_dagor_nvapi_lib "${_dagor_nvapi_dir}/aarch64/nvapia64.lib")
  endif()
  if(EXISTS "${_dagor_nvapi_lib}")
    add_library(sdk::nvapi STATIC IMPORTED GLOBAL)
    set_target_properties(sdk::nvapi PROPERTIES IMPORTED_LOCATION "${_dagor_nvapi_lib}"
      INTERFACE_INCLUDE_DIRECTORIES "${_dagor_nvapi_dir}" INTERFACE_COMPILE_DEFINITIONS HAS_NVAPI)
    set(DAGOR_SDK_NVAPI_ROOT "${_dagor_nvapi_dir}")
  endif()
  unset(_dagor_nvapi_dir)
  unset(_dagor_nvapi_lib)
endif()
