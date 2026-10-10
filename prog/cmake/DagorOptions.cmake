# The build-tree options of the engine. One build tree is one variant: everything here applies to every target in the
# tree, and presets (CMakePresets.json) name the combinations that are used.
include_guard(GLOBAL)

include(DagorValidate)

# dagor_option(<name> <default> <doc> [CHOICES <value>...])
macro(dagor_option name default doc)
  set(${name} "${default}" CACHE STRING "${doc}")
  cmake_parse_arguments(_dagor_opt "" "" "CHOICES" ${ARGN})
  if(_dagor_opt_CHOICES)
    set_property(CACHE ${name} PROPERTY STRINGS ${_dagor_opt_CHOICES})
    dagor_check_choice(${name} "${${name}}" ${_dagor_opt_CHOICES})
  endif()
endmacro()

# a list of configurations (Dev, Rel, IRel, Dbg), empty for none
macro(dagor_config_option name default doc)
  set(${name} "${default}" CACHE STRING "${doc} (a list of Dev, Rel, IRel, Dbg)")
  foreach(_dagor_cfg IN LISTS ${name})
    dagor_check_choice(${name} "${_dagor_cfg}" Dev Rel IRel Dbg)
  endforeach()
endmacro()

# what the tree builds
dagor_option(DAGOR_VARIANT tests "What the engine tree builds: unit tests, the tools (cdk, editor, 3ds Max plugins), dargbox or all"
  CHOICES tests cdk editor maxplug dargbox all)
option(DAGOR_ADD_ALL "Add every engine library and program, not only those a target of the tree uses" OFF)
if(DAGOR_VARIANT STREQUAL "all")
  set(DAGOR_ADD_ALL ON)
endif()

# code generation; the tools are built with SSE2 on Windows and precise floating point (prog/tools/tools_setup.jam)
set(_dagor_tools_tree OFF)
if(DAGOR_VARIANT MATCHES "^(cdk|editor|maxplug|dargbox)$")
  set(_dagor_tools_tree ON)
endif()
set(_dagor_sse_default 2)
if(DAGOR_PLATFORM STREQUAL "macOS" OR DAGOR_ARCH STREQUAL "e2k"
   OR (DAGOR_PLATFORM STREQUAL "windows" AND NOT _dagor_tools_tree) OR (DAGOR_PLATFORM STREQUAL "linux" AND _dagor_tools_tree))
  set(_dagor_sse_default 4)
endif()
dagor_option(DAGOR_SSE ${_dagor_sse_default} "SSE level of x86_64 code: 2 or 4 (SSE4.1 + POPCNT)" CHOICES 2 4)
set(_dagor_fp_default fast)
if(_dagor_tools_tree)
  set(_dagor_fp_default precise)
endif()
dagor_option(DAGOR_FP_MODEL ${_dagor_fp_default} "Floating point model" CHOICES fast precise strict)
unset(_dagor_sse_default)
unset(_dagor_fp_default)
unset(_dagor_tools_tree)
dagor_option(DAGOR_CPP_STD 20 "C++ standard" CHOICES 20 23)
dagor_option(DAGOR_KERNEL_LINKAGE static "The kernel linked into each program (static) or shared as daKernel (dynamic)"
  CHOICES static dynamic)
dagor_config_option(DAGOR_EXCEPTIONS_CONFIGS "Dev;Dbg" "Configurations whose C++ code has exceptions enabled")
option(DAGOR_CATCH_SEH "Catch structured exceptions (/EHa) where exceptions are enabled (Windows)" OFF)
option(DAGOR_RTTI "C++ RTTI" OFF)
dagor_config_option(DAGOR_STACK_PROTECTION_CONFIGS "Dev;Dbg" "Configurations with stack protection")
dagor_config_option(DAGOR_CHECKED_CONTAINERS_CONFIGS "Dbg" "Configurations with bounds-checked containers (EASTL_DEBUG)")
set(_dagor_strict_aliasing ON)
if(DAGOR_PLATFORM MATCHES "^(windows|android)$" OR NOT DAGOR_FP_MODEL STREQUAL "fast")
  set(_dagor_strict_aliasing OFF)
endif()
option(DAGOR_STRICT_ALIASING "Type-based alias analysis (-fstrict-aliasing)" ${_dagor_strict_aliasing})
unset(_dagor_strict_aliasing)
option(DAGOR_FORCE_LOGS "Keep debug logs in Rel and IRel" OFF)
option(DAGOR_WARNINGS_AS_ERRORS "Treat warnings in strict (non third-party) code as errors" OFF)

# instrumentation and optimization
dagor_option(DAGOR_SANITIZE none "Sanitizer" CHOICES none address undefined thread leak memory)
dagor_option(DAGOR_LTO OFF "Link-time optimization: OFF, thin or full" CHOICES OFF thin full)
option(DAGOR_LTO_DEVIRT "Whole-program devirtualization with LTO" ON)
option(DAGOR_COVERAGE "Clang source-based code coverage" OFF)
option(DAGOR_UNITY_BUILD "Unity (jumbo) builds of the targets that allow it" OFF)
option(DAGOR_CLANG_TIDY "Run clang-tidy as part of the compile" OFF)

# the Linux GUI layer of programs with a GUI (engine/osApiWrappers/linuxGUI)
option(DAGOR_LINUX_X11 "X11 support of Linux GUI programs" ON)
option(DAGOR_LINUX_WAYLAND "Wayland support of Linux GUI programs" ON)

# features of game trees (jam's per-game globals)
option(DAGOR_BREAKPAD "Crash reports with breakpad" OFF)
option(DAGOR_SYNC_ASYNC_READ "Serve the dfa_* async file API with blocking reads instead of AIO (posix)" OFF)

# release stamping
option(DAGOR_BUILD_STAMP "Stamp programs with the configure date and time (CI); off, they say '*' and never relink for it" OFF)

if(DAGOR_COVERAGE AND NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  message(FATAL_ERROR "DAGOR_COVERAGE needs a clang compiler")
endif()
