# EASTL; its include dir is one of the base include dirs of every C++ compile (Dagor::BuildSettings)
dagor_glob_sources(sources DIRS source GLOB *.cpp)
list(APPEND sources mem.cpp snprintf.cpp)
if(DAGOR_ARCH STREQUAL "e2k")
  list(APPEND sources assert_e2k.cpp)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES include)
