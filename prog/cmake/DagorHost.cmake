# DAGOR_HOST_PLATFORM (windows, linux, macOS), DAGOR_HOST_ARCH (x86_64, arm64, e2k) and DAGOR_HOST_TAG
# (<platform>-<arch>) of the machine running CMake. Usable before project(), so the toolchain files include it too.
include_guard(GLOBAL)

if(CMAKE_HOST_WIN32)
  set(DAGOR_HOST_PLATFORM windows)
elseif(CMAKE_HOST_APPLE)
  set(DAGOR_HOST_PLATFORM macOS)
elseif(CMAKE_HOST_UNIX)
  set(DAGOR_HOST_PLATFORM linux)
else()
  message(FATAL_ERROR "Unsupported host system ${CMAKE_HOST_SYSTEM_NAME}")
endif()

cmake_host_system_information(RESULT _dagor_host_cpu QUERY OS_PLATFORM)
string(TOLOWER "${_dagor_host_cpu}" _dagor_host_cpu)
if(_dagor_host_cpu MATCHES "^(amd64|x86_64|x64)$")
  set(DAGOR_HOST_ARCH x86_64)
elseif(_dagor_host_cpu MATCHES "^(arm64|aarch64)$")
  set(DAGOR_HOST_ARCH arm64)
elseif(_dagor_host_cpu STREQUAL "e2k")
  set(DAGOR_HOST_ARCH e2k)
else()
  message(FATAL_ERROR "Unsupported host CPU '${_dagor_host_cpu}'")
endif()
unset(_dagor_host_cpu)

set(DAGOR_HOST_TAG "${DAGOR_HOST_PLATFORM}-${DAGOR_HOST_ARCH}")
