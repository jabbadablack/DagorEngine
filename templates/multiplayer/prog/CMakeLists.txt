cmake_minimum_required(VERSION 3.24)
project(@GAME_NAME@ LANGUAGES NONE)
if(DEFINED ENV{DAGOR_ENGINE_ROOT})
  set(DAGOR_ENGINE_ROOT "$ENV{DAGOR_ENGINE_ROOT}" CACHE PATH "Dagor engine checkout")
else()
  file(STRINGS "${CMAKE_CURRENT_SOURCE_DIR}/../application.blk" _engine_setting REGEX "^engineRoot:t=")
  string(REGEX REPLACE "^engineRoot:t=\"([^\"]*)\".*" "\\1" _engine_root "${_engine_setting}")
  set(DAGOR_ENGINE_ROOT "${_engine_root}" CACHE PATH "Dagor engine checkout")
endif()
get_filename_component(DAGOR_PROJECT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/.." ABSOLUTE)
set(DAGOR_ACTIVE_PROJECT "@GAME_NAME@" CACHE STRING "Active Dagor project")
include("${DAGOR_ENGINE_ROOT}/prog/_jBuild/cmake/DagorWorkspace.cmake")

file(GLOB_RECURSE GAME_SCRIPT_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.das" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/*.nut" "${CMAKE_CURRENT_SOURCE_DIR}/gameBase/*.blk")
set_property(TARGET @GAME_NAME@ APPEND PROPERTY SOURCES ${GAME_SCRIPT_SOURCES})

add_custom_target(@GAME_NAME@_server
  COMMAND "${Python3_EXECUTABLE}" "${DAGOR_ENGINE_ROOT}/prog/_jBuild/ide.py" build
    --project "@GAME_NAME@" ${_dagor_args} -- -sDedicated=yes -sTarget=projects/@GAME_NAME@-server
  USES_TERMINAL VERBATIM)
add_custom_target(@GAME_NAME@_server_code
  COMMAND "${Python3_EXECUTABLE}" "${DAGOR_ENGINE_ROOT}/prog/_jBuild/ide.py" build
    --project "@GAME_NAME@" ${_dagor_args} -- -sDedicated=yes -sTarget=projects/@GAME_NAME@-server
  USES_TERMINAL VERBATIM)
add_custom_command(TARGET @GAME_NAME@_server POST_BUILD
  COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/build.py"
    shaders assets gui vromfs levels --platform "${DAGOR_PLATFORM}" --arch "${DAGOR_ARCH}" --config "${DAGOR_CONFIG}"
  USES_TERMINAL VERBATIM)

foreach(_action clean rebuild)
  add_custom_target(@GAME_NAME@_server_${_action}
    COMMAND "${Python3_EXECUTABLE}" "${DAGOR_ENGINE_ROOT}/prog/_jBuild/ide.py" ${_action}
      --project "@GAME_NAME@" ${_dagor_args} -- -sDedicated=yes -sTarget=projects/@GAME_NAME@-server
    USES_TERMINAL VERBATIM)
endforeach()
