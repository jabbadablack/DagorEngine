# CMake is the portable IDE model. Jam remains the engine build system.
find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
set(DAGOR_ACTIVE_PROJECT "testGI" CACHE STRING "Project used for code analysis and the default build")
set(DAGOR_CONFIG "dev" CACHE STRING "Jam configuration")
set_property(CACHE DAGOR_CONFIG PROPERTY STRINGS dbg dev rel)
if(CMAKE_HOST_WIN32)
  set(_dagor_host windows)
elseif(CMAKE_HOST_APPLE)
  set(_dagor_host macOS)
else()
  set(_dagor_host linux)
endif()
set(DAGOR_PLATFORM "${_dagor_host}" CACHE STRING "Jam target platform")
set_property(CACHE DAGOR_PLATFORM PROPERTY STRINGS windows linux macOS)
set(DAGOR_ARCH "native" CACHE STRING "Jam architecture (native, x86_64 or arm64)")
set(DAGOR_JAM "" CACHE FILEPATH "Optional Jam executable override")
set(_dagor_script "${DAGOR_ENGINE_ROOT}/prog/_jBuild/ide.py")
if(DAGOR_PROJECT_DIRECTORY)
  execute_process(COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" register
    --directory "${DAGOR_PROJECT_DIRECTORY}" --name "${DAGOR_ACTIVE_PROJECT}"
    RESULT_VARIABLE _dagor_registered ERROR_VARIABLE _dagor_registration_error)
  if(NOT _dagor_registered EQUAL 0)
    message(FATAL_ERROR "Could not register the standalone game: ${_dagor_registration_error}")
  endif()
endif()
set(_dagor_args --platform "${DAGOR_PLATFORM}" --arch "${DAGOR_ARCH}" --config "${DAGOR_CONFIG}")
if(DAGOR_JAM)
  list(APPEND _dagor_args --jam "${DAGOR_JAM}")
endif()
execute_process(COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" generate
  --project "${DAGOR_ACTIVE_PROJECT}" ${_dagor_args} --output "${CMAKE_BINARY_DIR}"
  RESULT_VARIABLE _dagor_result OUTPUT_VARIABLE _dagor_output ERROR_VARIABLE _dagor_error)
if(NOT _dagor_result EQUAL 0)
  message(FATAL_ERROR "Jam IDE setup failed: ${_dagor_output}\n${_dagor_error}")
endif()
message(STATUS "${_dagor_output}")
include("${CMAKE_BINARY_DIR}/dagor-model.cmake")
# Use the actual selected Jam compiler for the IDE code model, without requiring
# Visual Studio's C++ targets or MSBuild on non-Windows hosts.
set(CMAKE_CXX_COMPILER "${DAGOR_COMPILER}" CACHE FILEPATH "Jam compiler" FORCE)
set(CMAKE_C_COMPILER "${DAGOR_COMPILER}" CACHE FILEPATH "Jam C compiler" FORCE)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)
enable_language(C CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS OFF)
add_library(dagor_index_only OBJECT EXCLUDE_FROM_ALL ${DAGOR_INDEX_SOURCES})
target_include_directories(dagor_index_only PRIVATE ${DAGOR_INDEX_INCLUDES})
target_compile_definitions(dagor_index_only PRIVATE ${DAGOR_INDEX_DEFINES})
target_compile_features(dagor_index_only PRIVATE cxx_std_20)
set_target_properties(dagor_index_only PROPERTIES FOLDER "IDE code model (build through Jam targets)")
foreach(_forced IN LISTS DAGOR_INDEX_FORCED)
  if(CMAKE_CXX_COMPILER_FRONTEND_VARIANT STREQUAL "MSVC")
    target_compile_options(dagor_index_only PRIVATE "/FI${_forced}")
  else()
    target_compile_options(dagor_index_only PRIVATE -include "${_forced}")
  endif()
endforeach()
foreach(_project IN LISTS DAGOR_PROJECT_NAMES)
  if(_project STREQUAL DAGOR_ACTIVE_PROJECT)
    set(_all ALL)
  else()
    set(_all)
  endif()
  add_custom_target(${_project} ${_all}
    COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" build --project "${_project}" ${_dagor_args}
    USES_TERMINAL VERBATIM)
  if(DAGOR_PROJECT_DIRECTORY)
    add_custom_target(${_project}_code
      COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" build --project "${_project}" ${_dagor_args}
      USES_TERMINAL VERBATIM)
    add_custom_command(TARGET ${_project} POST_BUILD
      COMMAND "${Python3_EXECUTABLE}" "${DAGOR_PROJECT_DIRECTORY}/prog/build.py"
        shaders assets gui vromfs levels --platform "${DAGOR_PLATFORM}" --arch "${DAGOR_ARCH}" --config "${DAGOR_CONFIG}"
      USES_TERMINAL VERBATIM)
  endif()
  foreach(_action clean rebuild run)
    add_custom_target(${_project}_${_action}
      COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" ${_action} --project "${_project}" ${_dagor_args}
      USES_TERMINAL VERBATIM)
  endforeach()
  add_dependencies(${_project}_run ${_project})
endforeach()
set(DAGOR_NEW_GAME_NAME "MyGame" CACHE STRING "Name for the new_dagor_game target")
set(DAGOR_NEW_GAME_TEMPLATE "singleplayer" CACHE STRING "Project template")
set_property(CACHE DAGOR_NEW_GAME_TEMPLATE PROPERTY STRINGS singleplayer multiplayer)
set(DAGOR_NEW_GAME_DIRECTORY "${DAGOR_ENGINE_ROOT}/../${DAGOR_NEW_GAME_NAME}" CACHE PATH "New project directory")
add_custom_target(new_dagor_game
  COMMAND "${Python3_EXECUTABLE}" "${_dagor_script}" new --name "${DAGOR_NEW_GAME_NAME}" --template "${DAGOR_NEW_GAME_TEMPLATE}" --directory "${DAGOR_NEW_GAME_DIRECTORY}" ${_dagor_args}
  USES_TERMINAL VERBATIM)
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${DAGOR_ENGINE_ROOT}/_output/ide/project-registry.json")
set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${DAGOR_JAMFILE}" "${_dagor_script}" "${DAGOR_ENGINE_ROOT}/prog/platform.jam")
message(STATUS "Default Jam target: ${DAGOR_ACTIVE_PROJECT}; executable: ${DAGOR_EXECUTABLE}")
message(STATUS "Debugger working directory: ${DAGOR_WORKING_DIRECTORY}")

add_custom_target(dagor_tools
  COMMAND "${Python3_EXECUTABLE}" "${DAGOR_ENGINE_ROOT}/dng.py" tools
  USES_TERMINAL VERBATIM)
