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
include(DagorSdk)

# assemblers, by extension as in jam: .asm/.nasm/.nas NASM, .masm MASM (Windows), .s/.S the GNU assembler (the C
# compiler; LLVM clang on Windows arm64). Enabled here, in the top-level directory, for every target of the tree.
set(CMAKE_ASM_NASM_SOURCE_FILE_EXTENSIONS asm nasm nas)
set(CMAKE_ASM_MASM_SOURCE_FILE_EXTENSIONS masm)
set(CMAKE_ASM_SOURCE_FILE_EXTENSIONS s S)
if(DAGOR_PLATFORM STREQUAL "windows" OR (DAGOR_PLATFORM STREQUAL "macOS" AND NOT DAGOR_ARCH STREQUAL "arm64"))
  dagor_require_sdk(nasm)
  find_program(CMAKE_ASM_NASM_COMPILER NAMES nasm PATHS "${DAGOR_SDK_NASM_ROOT}" NO_DEFAULT_PATH REQUIRED)
else()
  find_program(CMAKE_ASM_NASM_COMPILER NAMES nasm) # the distro's; the libraries with NASM sources need it
endif()
if(CMAKE_ASM_NASM_COMPILER)
  enable_language(ASM_NASM)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  if(DAGOR_ARCH STREQUAL "x86_64")
    enable_language(ASM_MASM)
  elseif(DAGOR_LLVM_DIR)
    set(CMAKE_ASM_COMPILER "${DAGOR_LLVM_DIR}/bin/clang.exe")
    set(CMAKE_ASM_COMPILER_TARGET aarch64-pc-windows-msvc)
    enable_language(ASM)
  endif()
else()
  enable_language(ASM)
endif()

if(DAGOR_PLATFORM MATCHES "^(macOS|iOS|tvOS)$")
  enable_language(OBJC OBJCXX)
endif()

include(DagorCompilerFlags)
include(DagorTargets)
include(DagorLicenses)
include(DagorCodegen)
include(DagorContent)
include(DagorHostTools)
include(DagorPython)
include(DagorTesting)

message(STATUS "Dagor: ${DAGOR_TARGET_TAG} ${DAGOR_CC} ${CMAKE_CXX_COMPILER_VERSION}, variant ${DAGOR_VARIANT}, "
               "deps cache ${DAGOR_DEPS_DIR}")
