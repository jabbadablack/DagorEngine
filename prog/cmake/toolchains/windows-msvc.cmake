# Windows with the MSVC compiler (cl.exe, link.exe, lib.exe) of the toolset found on the machine: DAGOR_MSVC_TOOLSET
# 14.44 (VS 2022 17.14, the default), 14.29 (VS 2019 16.11, for the 3ds Max 2023/2024 plugins) or 'latest'.
# No developer prompt (vcvars) is needed: the include and library dirs are passed to the tools on their command lines.
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/detect/msvc.cmake")
dagor_toolchain_forward(DAGOR_MSVC_DIR DAGOR_MSVC_TOOLSET DAGOR_WINSDK_DIR DAGOR_WINSDK_VERSION)

dagor_detect_msvc()
dagor_detect_winsdk()
dagor_msvc_arch("${DAGOR_ARCH}" _dagor_msvc_arch)

if(DAGOR_ARCH STREQUAL "x86_64")
  set(CMAKE_SYSTEM_PROCESSOR AMD64)
else()
  set(CMAKE_SYSTEM_PROCESSOR ARM64)
endif()
if(NOT DAGOR_ARCH STREQUAL DAGOR_HOST_ARCH)
  set(CMAKE_SYSTEM_NAME Windows)
  set(CMAKE_SYSTEM_VERSION 10.0)
endif()

set(_dagor_host Hostx64)
if(DAGOR_HOST_ARCH STREQUAL "arm64" AND EXISTS "${DAGOR_MSVC_DIR}/bin/Hostarm64")
  set(_dagor_host Hostarm64)
endif()
set(_dagor_bin "${DAGOR_MSVC_DIR}/bin/${_dagor_host}/${_dagor_msvc_arch}")
set(CMAKE_C_COMPILER "${_dagor_bin}/cl.exe")
set(CMAKE_CXX_COMPILER "${_dagor_bin}/cl.exe")
set(CMAKE_LINKER "${_dagor_bin}/link.exe")
set(CMAKE_AR "${_dagor_bin}/lib.exe")
set(CMAKE_ASM_MASM_COMPILER "${_dagor_bin}/ml64.exe")
set(CMAKE_RC_COMPILER "${DAGOR_WINSDK_BIN}/rc.exe")
set(CMAKE_MT "${DAGOR_WINSDK_BIN}/mt.exe")

set(_dagor_sdk_inc "${DAGOR_WINSDK_DIR}/Include/${DAGOR_WINSDK_RESOLVED_VERSION}")
set(_dagor_sdk_lib "${DAGOR_WINSDK_DIR}/Lib/${DAGOR_WINSDK_RESOLVED_VERSION}")
foreach(_dagor_lang C CXX)
  set(CMAKE_${_dagor_lang}_STANDARD_INCLUDE_DIRECTORIES
    "${DAGOR_MSVC_DIR}/include" "${_dagor_sdk_inc}/ucrt" "${_dagor_sdk_inc}/um" "${_dagor_sdk_inc}/shared")
endforeach()
set(DAGOR_TOOLCHAIN_LINKER_FLAGS "/machine:${_dagor_msvc_arch}")
foreach(_dagor_dir "${DAGOR_MSVC_DIR}/lib/${_dagor_msvc_arch}" "${_dagor_sdk_lib}/ucrt/${_dagor_msvc_arch}"
                   "${_dagor_sdk_lib}/um/${_dagor_msvc_arch}")
  string(APPEND DAGOR_TOOLCHAIN_LINKER_FLAGS " /LIBPATH:\"${_dagor_dir}\"")
endforeach()
set(DAGOR_TOOLCHAIN_RC_FLAGS
  "/nologo /x /i\"${_dagor_sdk_inc}/um\" /i\"${_dagor_sdk_inc}/shared\" /i\"${DAGOR_MSVC_DIR}/include\"")

unset(_dagor_lang)
unset(_dagor_dir)
unset(_dagor_host)
unset(_dagor_bin)
unset(_dagor_sdk_inc)
unset(_dagor_sdk_lib)
unset(_dagor_msvc_arch)
