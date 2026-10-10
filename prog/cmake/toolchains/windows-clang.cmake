# Windows with clang-cl and lld-link of the pinned LLVM, against the MSVC STL/CRT and the Windows SDK found on the
# machine. No developer prompt (vcvars) is needed: the toolset and SDK are passed to the tools on their command lines.
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")
include("${CMAKE_CURRENT_LIST_DIR}/detect/msvc.cmake")
dagor_toolchain_forward(DAGOR_LLVM_DIR DAGOR_MSVC_DIR DAGOR_MSVC_TOOLSET DAGOR_WINSDK_DIR DAGOR_WINSDK_VERSION)

dagor_toolchain_llvm()
dagor_detect_msvc()
dagor_detect_winsdk()
dagor_msvc_arch("${DAGOR_ARCH}" _dagor_msvc_arch)

if(DAGOR_ARCH STREQUAL "x86_64")
  set(_dagor_triple x86_64-pc-windows-msvc)
  set(CMAKE_SYSTEM_PROCESSOR AMD64)
else()
  set(_dagor_triple aarch64-pc-windows-msvc)
  set(CMAKE_SYSTEM_PROCESSOR ARM64)
endif()
if(NOT DAGOR_ARCH STREQUAL DAGOR_HOST_ARCH)
  set(CMAKE_SYSTEM_NAME Windows)
  set(CMAKE_SYSTEM_VERSION 10.0)
endif()

set(CMAKE_C_COMPILER "${DAGOR_LLVM_DIR}/bin/clang-cl.exe")
set(CMAKE_CXX_COMPILER "${DAGOR_LLVM_DIR}/bin/clang-cl.exe")
set(CMAKE_C_COMPILER_TARGET ${_dagor_triple})
set(CMAKE_CXX_COMPILER_TARGET ${_dagor_triple})
set(CMAKE_LINKER "${DAGOR_LLVM_DIR}/bin/lld-link.exe")
set(CMAKE_AR "${DAGOR_LLVM_DIR}/bin/llvm-lib.exe")
set(CMAKE_RC_COMPILER "${DAGOR_WINSDK_BIN}/rc.exe")
set(CMAKE_MT "${DAGOR_WINSDK_BIN}/mt.exe")
set(CMAKE_ASM_MASM_COMPILER "${DAGOR_MSVC_DIR}/bin/Hostx64/${_dagor_msvc_arch}/ml64.exe")

# the toolset, SDK and the clang runtime libs (builtins, sanitizers, profile) for every compile and link
set(_dagor_sdk_inc "${DAGOR_WINSDK_DIR}/Include/${DAGOR_WINSDK_RESOLVED_VERSION}")
string(REGEX MATCH "^[0-9]+" _dagor_clang_major "${DAGOR_LLVM_VERSION}")
set(DAGOR_TOOLCHAIN_C_FLAGS
  "/vctoolsdir \"${DAGOR_MSVC_DIR}\" /winsdkdir \"${DAGOR_WINSDK_DIR}\" /winsdkversion ${DAGOR_WINSDK_RESOLVED_VERSION}")
set(DAGOR_TOOLCHAIN_CXX_FLAGS "${DAGOR_TOOLCHAIN_C_FLAGS}")
set(DAGOR_TOOLCHAIN_LINKER_FLAGS
  "/machine:${_dagor_msvc_arch} /vctoolsdir:\"${DAGOR_MSVC_DIR}\" /winsdkdir:\"${DAGOR_WINSDK_DIR}\" /winsdkversion:${DAGOR_WINSDK_RESOLVED_VERSION} /libpath:\"${DAGOR_LLVM_DIR}/lib/clang/${_dagor_clang_major}/lib/windows\"")
set(DAGOR_TOOLCHAIN_RC_FLAGS
  "/nologo /x /i\"${_dagor_sdk_inc}/um\" /i\"${_dagor_sdk_inc}/shared\" /i\"${DAGOR_MSVC_DIR}/include\"")

if(CMAKE_GENERATOR MATCHES "^Visual Studio")
  # MSBuild's ClangCL toolset with the pinned LLVM and lld-link; it passes the toolset and SDK dirs itself
  dagor_vs_generator(ClangCL "LLVMInstallDir=${DAGOR_LLVM_DIR}" "LLVMToolsVersion=${_dagor_clang_major}"
    "UseLldLink=true")
  set(DAGOR_TOOLCHAIN_C_FLAGS "")
  set(DAGOR_TOOLCHAIN_CXX_FLAGS "")
  set(DAGOR_TOOLCHAIN_LINKER_FLAGS "/libpath:\"${DAGOR_LLVM_DIR}/lib/clang/${_dagor_clang_major}/lib/windows\"")
endif()

unset(_dagor_triple)
unset(_dagor_sdk_inc)
unset(_dagor_clang_major)
unset(_dagor_msvc_arch)
