# Linux on Elbrus (e2k) with the MCST lcc compiler, whose GCC-compatible drivers are lcc/l++.
include("${CMAKE_CURRENT_LIST_DIR}/_common.cmake")

find_program(CMAKE_C_COMPILER NAMES lcc REQUIRED)
find_program(CMAKE_CXX_COMPILER NAMES l++ REQUIRED)
