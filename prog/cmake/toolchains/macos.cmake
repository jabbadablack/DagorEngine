# macOS with the Xcode clang selected by xcode-select (or DEVELOPER_DIR). DAGOR_ARCH x86_64, arm64 or universal
# (both in one binary); DAGOR_MACOS_MIN_VERSION is the deployment target.
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")
dagor_toolchain_forward(DAGOR_MACOS_MIN_VERSION)

execute_process(COMMAND xcrun --find clang OUTPUT_VARIABLE _dagor_clang OUTPUT_STRIP_TRAILING_WHITESPACE
                RESULT_VARIABLE _dagor_result ERROR_QUIET)
if(NOT _dagor_result EQUAL 0 OR NOT _dagor_clang)
  message(FATAL_ERROR "Xcode was not found: install it from the App Store and run 'xcode-select -s /Applications/Xcode.app'")
endif()
execute_process(COMMAND xcrun --find clang++ OUTPUT_VARIABLE _dagor_clangxx OUTPUT_STRIP_TRAILING_WHITESPACE)

set(CMAKE_C_COMPILER "${_dagor_clang}")
set(CMAKE_CXX_COMPILER "${_dagor_clangxx}")
set(CMAKE_OBJC_COMPILER "${_dagor_clang}")
set(CMAKE_OBJCXX_COMPILER "${_dagor_clangxx}")

if(NOT DAGOR_MACOS_MIN_VERSION)
  set(DAGOR_MACOS_MIN_VERSION 11.0)
endif()
set(CMAKE_OSX_DEPLOYMENT_TARGET "${DAGOR_MACOS_MIN_VERSION}" CACHE STRING "Minimum macOS version")
if(DAGOR_ARCH STREQUAL "universal")
  set(CMAKE_OSX_ARCHITECTURES "x86_64;arm64" CACHE STRING "")
else()
  set(CMAKE_OSX_ARCHITECTURES "${DAGOR_ARCH}" CACHE STRING "")
endif()
if(NOT DAGOR_ARCH STREQUAL DAGOR_HOST_ARCH)
  set(CMAKE_SYSTEM_NAME Darwin)
  set(CMAKE_SYSTEM_PROCESSOR "${DAGOR_ARCH}")
endif()

unset(_dagor_clang)
unset(_dagor_clangxx)
unset(_dagor_result)
