# Dng Empty: a daNetGame game. engine.blk names the engine checkout (DAGOR_ENGINE_ROOT overrides it); configure with
# a preset: cmake --preset windows-client (cmake --list-presets shows them).
cmake_minimum_required(VERSION 4.0)

if(NOT DAGOR_ENGINE_ROOT)
  file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/engine.blk" _engine REGEX "^[ \t]*engineRoot[ \t]*:[ \t]*t[ \t]*=")
  if(NOT _engine MATCHES "\"([^\"]*)\"")
    message(FATAL_ERROR "engine.blk: expected engineRoot:t=\"<path to the engine checkout>\"")
  endif()
  string(REGEX REPLACE "~(.)" "\\1" _engine "${CMAKE_MATCH_1}") # ~ escapes in BLK strings
  cmake_path(ABSOLUTE_PATH _engine BASE_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}" NORMALIZE OUTPUT_VARIABLE _engine)
  set(DAGOR_ENGINE_ROOT "${_engine}")
  unset(_engine)
endif()
if(NOT EXISTS "${DAGOR_ENGINE_ROOT}/prog/cmake/DagorBootstrap.cmake")
  message(FATAL_ERROR "${DAGOR_ENGINE_ROOT} is not a Dagor Engine checkout with the CMake build; set engineRoot in "
                      "engine.blk (or DAGOR_ENGINE_ROOT) to the engine dir")
endif()
include("${DAGOR_ENGINE_ROOT}/prog/cmake/DagorBootstrap.cmake")
project(dng_empty LANGUAGES C CXX)
include(DagorEngine)

add_subdirectory(prog)

dagor_finalize()
