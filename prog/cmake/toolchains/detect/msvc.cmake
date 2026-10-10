# MSVC toolset and Windows SDK detection for the Windows toolchain files. Visual Studio and the Windows SDK cannot be
# redistributed, so they are found on the machine; a missing one fails with what to install.
#
#   DAGOR_MSVC_TOOLSET    toolset version prefix: 14.44 (VS 2022 17.14, default), 14.29 (VS 2019 16.11), or 'latest'
#   DAGOR_MSVC_DIR        result: <VS>/VC/Tools/MSVC/<version>; can be set directly instead
#   DAGOR_MSVC_VERSION    result: the full toolset version (14.44.35207)
#   DAGOR_WINSDK_VERSION  Windows 10 SDK version: 10.0.19041.0 (default) or 'latest'
#   DAGOR_WINSDK_DIR      result: the Windows Kits/10 root; can be set directly instead

set(_dagor_vs_components
  "Microsoft.VisualStudio.Component.VC.14.44.17.14.x86.x64 Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64"
  "Microsoft.VisualStudio.Component.Windows10SDK.19041")

# dagor_msvc_arch(<arch> <out-var>): the MSVC name of a DAGOR_ARCH
function(dagor_msvc_arch arch out)
  if(arch STREQUAL "x86_64")
    set(${out} x64 PARENT_SCOPE)
  elseif(arch STREQUAL "arm64")
    set(${out} arm64 PARENT_SCOPE)
  else()
    message(FATAL_ERROR "No MSVC architecture for DAGOR_ARCH=${arch}")
  endif()
endfunction()

# newest dir in <dirs> by version, its name as the version
function(_dagor_newest_version_dir out)
  set(best "")
  set(best_version "0")
  foreach(dir IN LISTS ARGN)
    cmake_path(GET dir FILENAME version)
    if(version VERSION_GREATER best_version)
      set(best "${dir}")
      set(best_version "${version}")
    endif()
  endforeach()
  set(${out} "${best}" PARENT_SCOPE)
endfunction()

function(dagor_detect_msvc)
  set(DAGOR_MSVC_TOOLSET 14.44 CACHE STRING "MSVC toolset version prefix (14.44, 14.29) or 'latest'")
  dagor_msvc_arch("${DAGOR_ARCH}" target)
  if(NOT DAGOR_MSVC_DIR)
    set(pf86 "ProgramFiles(x86)")
    set(vswhere "$ENV{${pf86}}/Microsoft Visual Studio/Installer/vswhere.exe")
    set(installs)
    if(EXISTS "${vswhere}")
      execute_process(COMMAND "${vswhere}" -all -products * -format value -property installationPath
                      OUTPUT_VARIABLE installs OUTPUT_STRIP_TRAILING_WHITESPACE)
      string(REPLACE "\r" "" installs "${installs}")
      string(REPLACE "\n" ";" installs "${installs}")
    endif()
    set(found)
    foreach(install IN LISTS installs)
      file(TO_CMAKE_PATH "${install}" install)
      if(DAGOR_MSVC_TOOLSET STREQUAL "latest")
        file(GLOB dirs LIST_DIRECTORIES true "${install}/VC/Tools/MSVC/*")
      else()
        file(GLOB dirs LIST_DIRECTORIES true "${install}/VC/Tools/MSVC/${DAGOR_MSVC_TOOLSET}.*")
      endif()
      foreach(dir IN LISTS dirs)
        if(EXISTS "${dir}/lib/${target}/libcmt.lib")
          list(APPEND found "${dir}")
        endif()
      endforeach()
    endforeach()
    _dagor_newest_version_dir(dir ${found})
    if(NOT dir)
      list(GET _dagor_vs_components 0 components)
      message(FATAL_ERROR "MSVC toolset ${DAGOR_MSVC_TOOLSET} with ${target} libraries was not found in any Visual "
        "Studio installation. Install Visual Studio 2022 or its Build Tools with the components: ${components} "
        "(or choose another toolset with -DDAGOR_MSVC_TOOLSET=latest|14.29).")
    endif()
    set(DAGOR_MSVC_DIR "${dir}" CACHE PATH "MSVC toolset dir" FORCE)
  endif()
  cmake_path(GET DAGOR_MSVC_DIR FILENAME version)
  set(DAGOR_MSVC_VERSION "${version}" CACHE INTERNAL "")
endfunction()

function(dagor_detect_winsdk)
  set(DAGOR_WINSDK_VERSION 10.0.19041.0 CACHE STRING "Windows 10 SDK version or 'latest'")
  dagor_msvc_arch("${DAGOR_ARCH}" target)
  if(NOT DAGOR_WINSDK_DIR)
    cmake_host_system_information(RESULT root QUERY WINDOWS_REGISTRY
      "HKLM/SOFTWARE/Microsoft/Windows Kits/Installed Roots" VALUE KitsRoot10 VIEW 64_32 ERROR_VARIABLE error)
    if(NOT root)
      set(pf86 "ProgramFiles(x86)")
      set(root "$ENV{${pf86}}/Windows Kits/10")
    endif()
    file(TO_CMAKE_PATH "${root}" root)
    string(REGEX REPLACE "/+$" "" root "${root}")
    set(DAGOR_WINSDK_DIR "${root}" CACHE PATH "Windows Kits/10 root" FORCE)
  endif()
  set(version "${DAGOR_WINSDK_VERSION}")
  if(version STREQUAL "latest")
    file(GLOB dirs LIST_DIRECTORIES true "${DAGOR_WINSDK_DIR}/Lib/10.*")
    set(found)
    foreach(dir IN LISTS dirs)
      if(EXISTS "${dir}/um/${target}/kernel32.lib")
        list(APPEND found "${dir}")
      endif()
    endforeach()
    _dagor_newest_version_dir(dir ${found})
    cmake_path(GET dir FILENAME version)
  endif()
  if(NOT version OR NOT EXISTS "${DAGOR_WINSDK_DIR}/Include/${version}/um/windows.h"
     OR NOT EXISTS "${DAGOR_WINSDK_DIR}/Lib/${version}/um/${target}/kernel32.lib")
    list(GET _dagor_vs_components 1 components)
    message(FATAL_ERROR "Windows SDK ${DAGOR_WINSDK_VERSION} for ${target} was not found in '${DAGOR_WINSDK_DIR}'. "
      "Install it with the Visual Studio Installer (component ${components}), or choose another one with "
      "-DDAGOR_WINSDK_VERSION=latest|10.0.<build>.0.")
  endif()
  set(DAGOR_WINSDK_RESOLVED_VERSION "${version}" CACHE INTERNAL "")
  set(bin "${DAGOR_WINSDK_DIR}/bin/${version}/x64")
  if(DAGOR_HOST_ARCH STREQUAL "arm64" AND EXISTS "${DAGOR_WINSDK_DIR}/bin/${version}/arm64/rc.exe")
    set(bin "${DAGOR_WINSDK_DIR}/bin/${version}/arm64")
  endif()
  set(DAGOR_WINSDK_BIN "${bin}" CACHE INTERNAL "")
endfunction()

# dagor_vs_generator(<toolset> [<key>=<value>...]): for the Visual Studio generators, which build with MSBuild's own
# tools instead of CMAKE_<LANG>_COMPILER: selects the Visual Studio instance, the toolset (v143, v142, ClangCL) at
# DAGOR_MSVC_VERSION, the Windows SDK and the architecture of the detected ones. MSBuild then passes the toolset's and
# SDK's include and library dirs itself. The key=value pairs become MSBuild properties of every project.
function(dagor_vs_generator toolset)
  cmake_path(GET DAGOR_MSVC_DIR PARENT_PATH instance) # <VS>/VC/Tools/MSVC/<version>
  foreach(i RANGE 2)
    cmake_path(GET instance PARENT_PATH instance)
  endforeach()
  if(toolset STREQUAL "ClangCL" AND NOT EXISTS "${instance}/MSBuild/Microsoft/VC/v170/Platforms/x64/PlatformToolsets/ClangCL")
    message(FATAL_ERROR "The Visual Studio generator with clang-cl needs MSBuild's ClangCL toolset, which '${instance}' "
      "does not have. Install it with the Visual Studio Installer (component "
      "Microsoft.VisualStudio.Component.VC.Llvm.ClangToolset; the build still uses the pinned LLVM), or use the "
      "windows-msvc-* presets or the default Ninja generator.")
  endif()
  set(host x64)
  if(DAGOR_HOST_ARCH STREQUAL "arm64")
    set(host ARM64)
  endif()
  set(platform x64)
  if(DAGOR_ARCH STREQUAL "arm64")
    set(platform ARM64)
  endif()
  # -T and -A on the command line win (CMake caches them before the toolchain file runs)
  if(NOT CMAKE_GENERATOR_INSTANCE)
    set(CMAKE_GENERATOR_INSTANCE "${instance}" CACHE INTERNAL "")
  endif()
  if(NOT CMAKE_GENERATOR_TOOLSET)
    set(CMAKE_GENERATOR_TOOLSET "${toolset},version=${DAGOR_MSVC_VERSION},host=${host}" CACHE INTERNAL "")
  endif()
  if(NOT CMAKE_GENERATOR_PLATFORM)
    set(CMAKE_GENERATOR_PLATFORM "${platform},version=${DAGOR_WINSDK_RESOLVED_VERSION}" CACHE INTERNAL "")
  endif()
  set(CMAKE_VS_GLOBALS ${ARGN} PARENT_SCOPE)
endfunction()
