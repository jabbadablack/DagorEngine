# Included by a top-level CMakeLists.txt (the engine's or a project's) before project():
#
#   cmake_minimum_required(VERSION 4.0)
#   include(<engine>/prog/cmake/DagorBootstrap.cmake)
#   project(<name> C CXX)
#   include(DagorEngine)
#   ...
#   dagor_finalize()
#
# It settles what must be known before the first project() call: the engine root, the deps cache, the target
# platform/arch/compiler, the toolchain file and the build configurations.
include_guard(GLOBAL)

if(DEFINED PROJECT_NAME)
  message(FATAL_ERROR "DagorBootstrap.cmake must be included before the first project() call")
endif()

cmake_path(GET CMAKE_CURRENT_LIST_DIR PARENT_PATH DAGOR_ENGINE_ROOT) # prog/cmake -> prog
cmake_path(GET DAGOR_ENGINE_ROOT PARENT_PATH DAGOR_ENGINE_ROOT)
set(DAGOR_ENGINE_ROOT "${DAGOR_ENGINE_ROOT}" CACHE INTERNAL "Dagor engine checkout")
set(DAGOR_CMAKE_DIR "${DAGOR_ENGINE_ROOT}/prog/cmake" CACHE INTERNAL "Dagor CMake modules")
list(PREPEND CMAKE_MODULE_PATH "${DAGOR_CMAKE_DIR}")

include("${DAGOR_CMAKE_DIR}/DagorHost.cmake")

# the per-user cache of fetched SDKs, toolchains and the codegen venv, shared by every clone, worktree and project
if(NOT DAGOR_DEPS_DIR)
  if(DEFINED ENV{DAGOR_DEPS_DIR} AND NOT "$ENV{DAGOR_DEPS_DIR}" STREQUAL "")
    set(_dagor_deps "$ENV{DAGOR_DEPS_DIR}")
  elseif(CMAKE_HOST_WIN32)
    set(_dagor_deps "$ENV{LOCALAPPDATA}/dagor")
  elseif(CMAKE_HOST_APPLE)
    set(_dagor_deps "$ENV{HOME}/Library/Caches/dagor")
  elseif(DEFINED ENV{XDG_CACHE_HOME} AND NOT "$ENV{XDG_CACHE_HOME}" STREQUAL "")
    set(_dagor_deps "$ENV{XDG_CACHE_HOME}/dagor")
  else()
    set(_dagor_deps "$ENV{HOME}/.cache/dagor")
  endif()
  file(TO_CMAKE_PATH "${_dagor_deps}" _dagor_deps)
  set(DAGOR_DEPS_DIR "${_dagor_deps}" CACHE PATH "Cache of fetched SDKs, toolchains and the codegen Python venv")
  unset(_dagor_deps)
endif()

# target selection; presets set these, the defaults build for the host
set(DAGOR_PLATFORM "${DAGOR_HOST_PLATFORM}" CACHE STRING "Target platform")
set_property(CACHE DAGOR_PLATFORM PROPERTY STRINGS windows linux macOS iOS tvOS android)
set(DAGOR_ARCH "${DAGOR_HOST_ARCH}" CACHE STRING "Target architecture")
set_property(CACHE DAGOR_ARCH PROPERTY STRINGS x86_64 arm64 e2k universal)

set(_dagor_default_compiler clang)
if(DAGOR_PLATFORM STREQUAL "linux")
  set(_dagor_default_compiler gcc)
  if(DAGOR_ARCH STREQUAL "e2k")
    set(_dagor_default_compiler lcc)
  endif()
endif()
set(DAGOR_COMPILER "${_dagor_default_compiler}" CACHE STRING "Compiler family: clang (clang-cl on Windows), msvc, gcc, lcc")
unset(_dagor_default_compiler)
set_property(CACHE DAGOR_COMPILER PROPERTY STRINGS clang msvc gcc lcc)

include("${DAGOR_CMAKE_DIR}/DagorValidate.cmake")
dagor_validate_target("${DAGOR_PLATFORM}" "${DAGOR_ARCH}" "${DAGOR_COMPILER}")

if(NOT CMAKE_TOOLCHAIN_FILE)
  string(TOLOWER "${DAGOR_PLATFORM}" _dagor_tc)
  if(_dagor_tc MATCHES "^(windows|linux)$")
    string(APPEND _dagor_tc "-${DAGOR_COMPILER}")
  endif()
  set(CMAKE_TOOLCHAIN_FILE "${DAGOR_CMAKE_DIR}/toolchains/${_dagor_tc}.cmake" CACHE FILEPATH "Toolchain file")
  unset(_dagor_tc)
endif()

# replaces CMake's default compiler and linker flags with none: Dagor::BuildSettings states every flag
set(CMAKE_USER_MAKE_RULES_OVERRIDE "${DAGOR_CMAKE_DIR}/DagorFlagOverrides.cmake")

# dev (DAGOR_DBGLEVEL 1, optimized, logs and asserts), rel (0), irel (-1, no logs at all), dbg (2, unoptimized)
get_property(_dagor_multi_config GLOBAL PROPERTY GENERATOR_IS_MULTI_CONFIG)
if(_dagor_multi_config OR CMAKE_GENERATOR MATCHES "Multi-Config|Visual Studio|Xcode")
  set(CMAKE_CONFIGURATION_TYPES "Dev;Rel;IRel;Dbg" CACHE STRING "Build configurations")
  if(CMAKE_GENERATOR MATCHES "Ninja Multi-Config")
    set(CMAKE_DEFAULT_BUILD_TYPE Dev CACHE STRING "Configuration of a plain cmake --build")
  endif()
else()
  set(CMAKE_BUILD_TYPE Dev CACHE STRING "Build configuration: Dev, Rel, IRel or Dbg")
  set_property(CACHE CMAKE_BUILD_TYPE PROPERTY STRINGS Dev Rel IRel Dbg)
endif()
unset(_dagor_multi_config)

# the objects of Windows builds under hashed dir and file names: the engine dirs of a project tree are deep enough for
# the full names to pass MAX_PATH (CMake 4.2)
if(CMAKE_HOST_WIN32 AND CMAKE_VERSION VERSION_GREATER_EQUAL 4.2)
  set(CMAKE_INTERMEDIATE_DIR_STRATEGY SHORT CACHE STRING "Target intermediate dirs: FULL or SHORT (hashed names)")
endif()

# a compiler cache (sccache, then ccache) for the Ninja and Makefile generators
set(DAGOR_COMPILER_LAUNCHER auto CACHE STRING "Compiler cache: auto, none or a path")
if(NOT CMAKE_GENERATOR MATCHES "Visual Studio|Xcode" AND NOT DAGOR_COMPILER_LAUNCHER STREQUAL "none"
   AND NOT CMAKE_CXX_COMPILER_LAUNCHER)
  if(DAGOR_COMPILER_LAUNCHER STREQUAL "auto")
    find_program(DAGOR_COMPILER_LAUNCHER_PATH NAMES sccache ccache DOC "Compiler cache used by the build")
  else()
    set(DAGOR_COMPILER_LAUNCHER_PATH "${DAGOR_COMPILER_LAUNCHER}")
  endif()
  if(DAGOR_COMPILER_LAUNCHER_PATH)
    set(CMAKE_C_COMPILER_LAUNCHER "${DAGOR_COMPILER_LAUNCHER_PATH}")
    set(CMAKE_CXX_COMPILER_LAUNCHER "${DAGOR_COMPILER_LAUNCHER_PATH}")
  endif()
endif()

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
