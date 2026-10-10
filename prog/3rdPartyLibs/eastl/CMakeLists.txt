# EASTL; its include dir is one of the base include dirs of every C++ compile (Dagor::BuildSettings). Flavor kernel:
# the build inside daKernel (tools/libTools/daKernel), which exports its allocator and snprintf (__B_KERNEL_LIB).
function(_eastl flavor)
  set(defines)
  if(flavor STREQUAL "kernel")
    set(defines __B_KERNEL_LIB)
  elseif(flavor)
    message(FATAL_ERROR "3rdPartyLibs/eastl has no flavor '${flavor}'")
  endif()
  dagor_glob_sources(sources DIRS source GLOB *.cpp)
  list(APPEND sources mem.cpp snprintf.cpp)
  if(DAGOR_ARCH STREQUAL "e2k")
    list(APPEND sources assert_e2k.cpp)
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} SOURCES ${sources} PRIVATE_INCLUDES include PRIVATE_DEFINES ${defines})
endfunction()

dagor_flavors(_eastl)
