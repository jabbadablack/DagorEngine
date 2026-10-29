cmake_minimum_required(VERSION 3.24)
project(DagorEngine LANGUAGES NONE)
get_filename_component(DAGOR_ENGINE_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
include("${CMAKE_CURRENT_SOURCE_DIR}/cmake/DagorWorkspace.cmake")
