# The engine's host tools (the CDK: shader compilers, vromfsPacker, ...) for trees that run them at build time.
#
# dagor_host_tool(<tool> <out-var> [DIR <engine dir>]) sets <out-var> to the program to run and adds what makes it
# exist:
#   - with DIR (the engine dir that declares <tool>), in a tree that is not cross-compiling: the tree's own target;
#   - with DAGOR_HOST_TOOLS_DIR (a CDK, e.g. tools/dagor_cdk/windows-x86_64 of a prebuilt engine), the program there;
#   - otherwise the host CDK of this engine, built on demand: target dagor.hostTools configures and builds the engine's
#     cdk tree for the host in <engine>/build/host-cdk-<host> and installs it into <engine>/tools/dagor_cdk/<host>
#     (DAGOR_HOST_TOOLS_CONFIG, Dev by default). Trees sharing that tree (projects, cross builds) build it under a lock,
#     one at a time; when it is up to date that is a quick check.
# A custom command running the tool lists ${<out-var>_DEPENDS} in its DEPENDS.
include_guard(GLOBAL)

set(DAGOR_HOST_TOOLS_DIR "" CACHE PATH "A CDK (prebuilt engine tools) for the build steps; empty builds the engine's")
set(DAGOR_HOST_TOOLS_CONFIG Dev CACHE STRING "Configuration of the host tools built on demand")
set_property(CACHE DAGOR_HOST_TOOLS_CONFIG PROPERTY STRINGS Dev Rel IRel Dbg)
set(DAGOR_HOST_TOOLS_SCRIPT "${CMAKE_CURRENT_LIST_DIR}/scripts/build_host_tools.cmake")

# the CDK tools jam built rel only, without a config postfix (NO_CONFIG_POSTFIX; the cdk tree checks this list)
set(_DAGOR_CDK_NO_POSTFIX binBlk ddsx2dds ddsxCvt dolphin whale duktape)

# the file name of a CDK program built in <config>: <tool>-<config postfix>[.exe]; rel-only tools have no postfix
function(_dagor_host_tool_file tool config out)
  set(postfix_Dev -dev)
  set(postfix_Dbg -dbg)
  set(postfix_IRel -irel)
  set(postfix_Rel "")
  set(name "${tool}${postfix_${config}}")
  if(tool IN_LIST _DAGOR_CDK_NO_POSTFIX)
    set(name "${tool}")
  endif()
  if(CMAKE_HOST_WIN32)
    string(APPEND name ".exe")
  endif()
  set(${out} "${name}" PARENT_SCOPE)
endfunction()

function(dagor_host_tool tool out)
  cmake_parse_arguments(PARSE_ARGV 2 arg "" "DIR" "")
  if(arg_DIR AND NOT CMAKE_CROSSCOMPILING)
    dagor_use("${arg_DIR}")
    set(${out} "$<TARGET_FILE:${tool}>" PARENT_SCOPE)
    set(${out}_DEPENDS ${tool} PARENT_SCOPE)
    return()
  endif()
  if(DAGOR_HOST_TOOLS_DIR)
    _dagor_host_tool_file(${tool} Dev file)
    if(NOT EXISTS "${DAGOR_HOST_TOOLS_DIR}/${file}")
      _dagor_host_tool_file(${tool} Rel file)
    endif()
    if(NOT EXISTS "${DAGOR_HOST_TOOLS_DIR}/${file}")
      message(FATAL_ERROR "DAGOR_HOST_TOOLS_DIR='${DAGOR_HOST_TOOLS_DIR}' has no ${tool}")
    endif()
    set(${out} "${DAGOR_HOST_TOOLS_DIR}/${file}" PARENT_SCOPE)
    set(${out}_DEPENDS "${DAGOR_HOST_TOOLS_DIR}/${file}" PARENT_SCOPE)
    return()
  endif()

  # the engine's host CDK, built by the dagor.hostTools target
  _dagor_host_tool_file(${tool} ${DAGOR_HOST_TOOLS_CONFIG} file)
  set(path "${DAGOR_ENGINE_ROOT}/tools/dagor_cdk/${DAGOR_HOST_TAG}/${file}")
  set_property(GLOBAL APPEND PROPERTY DAGOR_HOST_TOOLS "${tool}")
  set_property(GLOBAL APPEND PROPERTY DAGOR_HOST_TOOL_FILES "${path}")
  set(${out} "${path}" PARENT_SCOPE)
  set(${out}_DEPENDS dagor.hostTools PARENT_SCOPE)
endfunction()

# called by dagor_finalize(): the dagor.hostTools target, building the tools the tree asked for
function(_dagor_host_tools_target)
  get_property(tools GLOBAL PROPERTY DAGOR_HOST_TOOLS)
  if(NOT tools)
    return()
  endif()
  list(REMOVE_DUPLICATES tools)
  get_property(files GLOBAL PROPERTY DAGOR_HOST_TOOL_FILES)
  list(REMOVE_DUPLICATES files)
  list(JOIN tools "," tool_list)
  set(make_program "")
  if(CMAKE_GENERATOR MATCHES "Ninja")
    set(make_program "${CMAKE_MAKE_PROGRAM}") # the host tree uses the same Ninja
  endif()
  add_custom_target(dagor.hostTools
    COMMAND "${CMAKE_COMMAND}" -DENGINE_ROOT=${DAGOR_ENGINE_ROOT} -DHOST_TAG=${DAGOR_HOST_TAG}
      -DCONFIG=${DAGOR_HOST_TOOLS_CONFIG} -DTOOLS=${tool_list} -DDEPS_DIR=${DAGOR_DEPS_DIR}
      -DMAKE_PROGRAM=${make_program} -P "${DAGOR_HOST_TOOLS_SCRIPT}"
    BYPRODUCTS ${files}
    COMMENT "Host tools of ${DAGOR_ENGINE_ROOT} (${DAGOR_HOST_TAG}, ${DAGOR_HOST_TOOLS_CONFIG}): ${tools}"
    USES_TERMINAL
    VERBATIM)
  set_property(TARGET dagor.hostTools PROPERTY FOLDER "tools")
endfunction()

# called by dagor_finalize(): the CDK tools of this tree are named as dagor_host_tool() expects
function(_dagor_check_cdk_names)
  get_property(targets GLOBAL PROPERTY DAGOR_CDK_TARGETS)
  foreach(target IN LISTS targets)
    get_property(postfix TARGET ${target} PROPERTY DEV_POSTFIX)
    if(target IN_LIST _DAGOR_CDK_NO_POSTFIX AND postfix)
      message(FATAL_ERROR "CDK tool ${target} has a config postfix: remove it from _DAGOR_CDK_NO_POSTFIX "
        "(DagorHostTools.cmake)")
    elseif(NOT target IN_LIST _DAGOR_CDK_NO_POSTFIX AND NOT postfix)
      message(FATAL_ERROR "CDK tool ${target} is built without a config postfix: add it to _DAGOR_CDK_NO_POSTFIX "
        "(DagorHostTools.cmake)")
    endif()
  endforeach()
endfunction()
