# cmake -DSOURCE_DIR=<game> -DTREE=<tree> -DTARGET=<game>-aot -DENGINE_ROOT=<engine> [-DDEPS_DIR=<dir>]
#       [-DMAKE_PROGRAM=<ninja>] -P build_das_aot_compiler.cmake
# Builds the daScript AOT compiler of a game (see DagorDas.cmake): configures the game's source tree for the host with
# DAGOR_DAS_AOT_COMPILER once (<tree>), and builds the compiler in Dev, into <tree>/bin. A lock keeps the game's trees
# that share it from building it at the same time.
foreach(var SOURCE_DIR TREE TARGET ENGINE_ROOT)
  if(NOT ${var})
    message(FATAL_ERROR "build_das_aot_compiler.cmake: ${var} is not set")
  endif()
endforeach()
cmake_path(GET TREE PARENT_PATH parent)
file(MAKE_DIRECTORY "${parent}")
file(LOCK "${TREE}.lock" TIMEOUT 14400 RESULT_VARIABLE locked)
if(locked)
  message(FATAL_ERROR "Cannot lock ${TREE}.lock: ${locked}")
endif()

function(run)
  execute_process(COMMAND ${ARGN} RESULT_VARIABLE result)
  if(result)
    list(JOIN ARGN " " command)
    message(FATAL_ERROR "daScript AOT compiler: '${command}' failed (${result})")
  endif()
endfunction()

if(NOT EXISTS "${TREE}/CMakeCache.txt")
  set(args -S "${SOURCE_DIR}" -B "${TREE}" -G "Ninja Multi-Config" -DDAGOR_VARIANT=game -DDAGOR_DAS_AOT_COMPILER=ON
    "-DDAGOR_ENGINE_ROOT=${ENGINE_ROOT}")
  if(DEPS_DIR)
    list(APPEND args "-DDAGOR_DEPS_DIR=${DEPS_DIR}")
  endif()
  if(MAKE_PROGRAM)
    list(APPEND args "-DCMAKE_MAKE_PROGRAM=${MAKE_PROGRAM}")
  endif()
  run("${CMAKE_COMMAND}" ${args})
endif()
run("${CMAKE_COMMAND}" --build "${TREE}" --config Dev --target "${TARGET}")
