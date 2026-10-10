# Linux with the distro's clang (clang/clang++, or clang-<N>/clang++-<N> with -DDAGOR_CLANG_VERSION=<N>).
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")
dagor_toolchain_forward(DAGOR_CLANG_VERSION)

set(_dagor_suffix "")
if(DAGOR_CLANG_VERSION)
  set(_dagor_suffix "-${DAGOR_CLANG_VERSION}")
endif()
find_program(CMAKE_C_COMPILER NAMES clang${_dagor_suffix} REQUIRED)
find_program(CMAKE_CXX_COMPILER NAMES clang++${_dagor_suffix} REQUIRED)
find_program(CMAKE_AR NAMES llvm-ar${_dagor_suffix} llvm-ar ar)
find_program(CMAKE_RANLIB NAMES llvm-ranlib${_dagor_suffix} llvm-ranlib ranlib)
unset(_dagor_suffix)
