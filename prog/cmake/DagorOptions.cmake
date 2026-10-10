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

# daScript ahead-of-time compilation of the game's scripts (to C++, or with LLVM to objects)
option(DAGOR_DAS_AOT "Compile the daScript game scripts ahead of time" OFF)
option(DAGOR_DAS_LLVM_AOT "daScript AOT through LLVM objects instead of C++" OFF)

# Quirrel variable tracing (dargbox's script debugging)
set(_dagor_sq_var_trace OFF)
if(DAGOR_VARIANT STREQUAL "dargbox")
  set(_dagor_sq_var_trace ON)
endif()
option(DAGOR_SQ_VAR_TRACE "Quirrel variable tracing" ${_dagor_sq_var_trace})
unset(_dagor_sq_var_trace)

# the 3d drivers of the tree's programs (jam's UseD3DMultiList): one is linked directly, several (or one with
# DAGOR_D3D_MULTI_FORCED) through the multi-driver interface (drv3d_pc_multi, _TARGET_D3D_MULTI)
set(_dagor_d3d_valid_windows null stub vulkan DX11 DX12)
set(_dagor_d3d_valid_linux null stub vulkan)
set(_dagor_d3d_valid_macOS null stub Metal)
set(DAGOR_D3D_DRIVERS stub CACHE STRING "3d drivers (a list of: ${_dagor_d3d_valid_${DAGOR_PLATFORM}})")
foreach(_dagor_drv IN LISTS DAGOR_D3D_DRIVERS)
  dagor_check_choice("DAGOR_D3D_DRIVERS for ${DAGOR_PLATFORM}" "${_dagor_drv}" ${_dagor_d3d_valid_${DAGOR_PLATFORM}})
endforeach()
set(_dagor_d3d_forced OFF)
if(DAGOR_VARIANT STREQUAL "tests")
  # the render tests use the multi-driver interface (d3di) even with the stub alone, as jam's tests did with their
  # driver lists (stub plus DX12/vulkan on Windows and Linux; macOS has no multi-driver Metal build)
  set(_dagor_d3d_forced ON)
endif()
option(DAGOR_D3D_MULTI_FORCED "The multi-driver interface even for a single driver" ${_dagor_d3d_forced})
list(LENGTH DAGOR_D3D_DRIVERS _dagor_d3d_count)
if(_dagor_d3d_count GREATER 1 OR DAGOR_D3D_MULTI_FORCED)
  set(DAGOR_D3D_MULTI ON)
else()
  set(DAGOR_D3D_MULTI OFF)
endif()
unset(_dagor_d3d_valid_windows)
unset(_dagor_d3d_valid_linux)
unset(_dagor_d3d_valid_macOS)
unset(_dagor_d3d_forced)
unset(_dagor_d3d_count)
unset(_dagor_drv)

# the shader system (engine/shaders): the tools' builds load a second bindump; games have their own camera code; the
# shaders' state code can be compiled to C++ (CppStcode) instead of being interpreted
set(_dagor_tools_default OFF)
if(DAGOR_VARIANT STREQUAL "editor")
  set(_dagor_tools_default ON)
endif()
option(DAGOR_BUILDING_TOOLS "The tree builds the editor tools (jam's BuildingTools: a second bindump, ...)" ${_dagor_tools_default})
unset(_dagor_tools_default)
option(DAGOR_SHADERS_CAM_STUB "engine/shaders brings its camera stub (off in games, which have their own)" ON)
# (jam's default was 'both': its test 'if $(CppStcode) in enable both' holds for an unset variable)
dagor_option(DAGOR_CPP_STCODE both "Shader state code as C++ (both: with the interpreted code as fallback), validate, disable"
  CHOICES both enable validate disable)
option(DAGOR_CPP_STCODE_BRANCHED "C++ state code with dynamic branching" OFF)
option(DAGOR_PROFILE_STCODE "Profile the shader state code" OFF)

# development features in the programs' non-Rel builds
option(DAGOR_NET_IMGUI "netImgui (remote ImGui) in the Dev, IRel and Dbg builds" ON)
option(DAGOR_FORCE_LINK_DEBUG_LINES "Keep the debug line drawing in Rel and IRel" OFF)

# features of game trees (jam's per-game globals)
option(DAGOR_DEDICATED "The tree builds a dedicated server (no rendering)" OFF)
option(DAGOR_STREAMLINE "NVIDIA Streamline (DLSS, Reflex) in the drivers (Windows)" OFF)
option(DAGOR_BREAKPAD "Crash reports with breakpad" OFF)
option(DAGOR_SYNC_ASYNC_READ "Serve the dfa_* async file API with blocking reads instead of AIO (posix)" OFF)

# release stamping
option(DAGOR_BUILD_STAMP "Stamp programs with the configure date and time (CI); off, they say '*' and never relink for it" OFF)

if(DAGOR_COVERAGE AND NOT CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  message(FATAL_ERROR "DAGOR_COVERAGE needs a clang compiler")
endif()
