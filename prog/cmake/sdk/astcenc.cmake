# ARM's ASTC encoder: DAGOR_SDK_ASTCENC_RUNTIME, the astcenc programs (one per instruction set; one universal binary on
# macOS) that the texture exporter runs, put next to the tools
dagor_fetch_sdk(astcenc _dagor_astcenc_dir)
set(DAGOR_SDK_ASTCENC_ROOT "${_dagor_astcenc_dir}")
file(GLOB _dagor_astcenc_runtime "${_dagor_astcenc_dir}/astcenc*") # the archives hold only bin/, which is stripped
if(NOT _dagor_astcenc_runtime)
  message(FATAL_ERROR "The astcenc SDK in '${_dagor_astcenc_dir}' has no astcenc programs")
endif()
# cached: the module runs once per configure, the variable is read in other scopes
set(DAGOR_SDK_ASTCENC_RUNTIME "${_dagor_astcenc_runtime}" CACHE INTERNAL "")
unset(_dagor_astcenc_dir)
unset(_dagor_astcenc_runtime)
