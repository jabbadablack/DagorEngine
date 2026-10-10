# include(DagorEngine) after project(): the options, build settings and functions of the engine's build. See
# DagorBootstrap.cmake for the layout of a top-level CMakeLists.txt.
include_guard(GLOBAL)

if(NOT DAGOR_ENGINE_ROOT)
  message(FATAL_ERROR "include prog/cmake/DagorBootstrap.cmake before project()")
endif()
if(NOT CMAKE_CXX_COMPILER_LOADED)
  message(FATAL_ERROR "The project() of a Dagor build must enable CXX (and C)")
endif()

set(DAGOR_TARGET_TAG "${DAGOR_PLATFORM}-${DAGOR_ARCH}")
set(DAGOR_CROSS_COMPILING OFF)
if(NOT DAGOR_TARGET_TAG STREQUAL DAGOR_HOST_TAG)
  set(DAGOR_CROSS_COMPILING ON)
endif()
# the data format code of the target's packed resources (jam's PlatformDataFormatCode)
if(DAGOR_PLATFORM STREQUAL "iOS")
  set(DAGOR_DATA_FORMAT iOS)
elseif(DAGOR_PLATFORM STREQUAL "android")
  set(DAGOR_DATA_FORMAT and)
else()
  set(DAGOR_DATA_FORMAT PC)
endif()

include(DagorOptions)
include(DagorCompilerFlags)
include(DagorTargets)
include(DagorSdk)
include(DagorPython)

message(STATUS "Dagor: ${DAGOR_TARGET_TAG} ${DAGOR_CC} ${CMAKE_CXX_COMPILER_VERSION}, variant ${DAGOR_VARIANT}, "
               "deps cache ${DAGOR_DEPS_DIR}")
