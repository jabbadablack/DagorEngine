# Linux with the distro's GCC (gcc/g++, or gcc-<N>/g++-<N> with -DDAGOR_GCC_VERSION=<N>).
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")
dagor_toolchain_forward(DAGOR_GCC_VERSION)

set(_dagor_suffix "")
if(DAGOR_GCC_VERSION)
  set(_dagor_suffix "-${DAGOR_GCC_VERSION}")
endif()
find_program(CMAKE_C_COMPILER NAMES gcc${_dagor_suffix} REQUIRED)
find_program(CMAKE_CXX_COMPILER NAMES g++${_dagor_suffix} REQUIRED)
# gcc-ar/gcc-ranlib understand the LTO objects of -flto
find_program(CMAKE_AR NAMES gcc-ar${_dagor_suffix} gcc-ar ar)
find_program(CMAKE_RANLIB NAMES gcc-ranlib${_dagor_suffix} gcc-ranlib ranlib)
unset(_dagor_suffix)
