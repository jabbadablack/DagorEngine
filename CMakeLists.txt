# The engine's own build: its unit tests (DAGOR_VARIANT=tests), tools (cdk, editor, maxplug), dargbox, or all of it.
# Games and samples are separate projects with their own top-level CMakeLists.txt (see templates/dng-empty).
# Configure with a preset: cmake --preset windows-tests (cmake --list-presets shows them).
cmake_minimum_required(VERSION 4.0)
include(prog/cmake/DagorBootstrap.cmake)
project(DagorEngine LANGUAGES C CXX)
include(DagorEngine)

if(DAGOR_VARIANT MATCHES "^(tests|all)$")
  dagor_use_tests()
endif()

dagor_finalize()
