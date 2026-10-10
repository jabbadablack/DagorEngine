# Catch2 3.8.0 (the engine's build of it replaces the upstream CMakeLists.txt; extras/Catch.cmake is upstream's CTest
# integration). Test programs get main() from <unittest/mainCatch2.inc.cpp>, see dagor_add_catch2_test().
dagor_glob_sources(sources GLOB *.cpp DIRS
  src/catch2
  src/catch2/benchmark
  src/catch2/benchmark/detail
  src/catch2/generators
  src/catch2/interfaces
  src/catch2/internal
  src/catch2/matchers
  src/catch2/matchers/internal
  src/catch2/reporters
)

dagor_add_library(
  SOURCES ${sources}
  PUBLIC_INCLUDES src
  PRIVATE_DEFINES CATCH_AMALGAMATED_CUSTOM_MAIN
  EXCEPTIONS ON
  LICENSE_FILES LICENSE.txt
  PROPERTIES SYSTEM ON # its headers are third-party code: the warnings of strict test code do not apply to them
)
