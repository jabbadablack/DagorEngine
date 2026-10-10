# cmake -DENGINE_ROOT=<engine> -DHOST_TAG=<host-arch> -DCONFIG=<config> -DTOOLS=<tool,...> [-DDEPS_DIR=<dir>]
#       [-DMAKE_PROGRAM=<ninja>] -P build_host_tools.cmake
# Builds the engine's host tools (see DagorHostTools.cmake): configures its cdk tree for the host once
# (<engine>/build/host-cdk-<host>), builds the tools and installs them into <engine>/tools/dagor_cdk/<host>. A lock
# keeps the trees that share it from building it at the same time.
foreach(var ENGINE_ROOT HOST_TAG CONFIG TOOLS)
  if(NOT ${var})
    message(FATAL_ERROR "build_host_tools.cmake: ${var} is not set")
  endif()
endforeach()
string(REPLACE "," ";" TOOLS "${TOOLS}")
set(tree "${ENGINE_ROOT}/build/host-cdk-${HOST_TAG}")
file(MAKE_DIRECTORY "${ENGINE_ROOT}/build")
file(LOCK "${tree}.lock" TIMEOUT 14400 RESULT_VARIABLE locked)
if(locked)
  message(FATAL_ERROR "Cannot lock ${tree}.lock: ${locked}")
endif()

function(run)
  execute_process(COMMAND ${ARGN} RESULT_VARIABLE result)
  if(result)
    list(JOIN ARGN " " command)
    message(FATAL_ERROR "Host tools: '${command}' failed (${result})")
  endif()
endfunction()

if(NOT EXISTS "${tree}/CMakeCache.txt")
  set(args -S "${ENGINE_ROOT}" -B "${tree}" -G "Ninja Multi-Config" -DDAGOR_VARIANT=cdk
    "-DCMAKE_INSTALL_PREFIX=${ENGINE_ROOT}")
  if(DEPS_DIR)
    list(APPEND args "-DDAGOR_DEPS_DIR=${DEPS_DIR}")
  endif()
  if(MAKE_PROGRAM)
    list(APPEND args "-DCMAKE_MAKE_PROGRAM=${MAKE_PROGRAM}")
  endif()
  run("${CMAKE_COMMAND}" ${args})
endif()
run("${CMAKE_COMMAND}" --build "${tree}" --config "${CONFIG}" --target ${TOOLS})
run("${CMAKE_COMMAND}" --install "${tree}" --config "${CONFIG}" --component cdk)
