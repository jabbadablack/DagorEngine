# dlmalloc 2.8.4, the default allocator of engine/memory on Windows; flavor 'debug' with the debug allocator checks
# (linked by engine/memory:dlmalloc.dbg and .dbg2)

function(_dlmalloc flavor)
  set(defines)
  if(flavor STREQUAL "debug")
    set(defines MEM_DEBUGALLOC)
  elseif(NOT flavor STREQUAL "")
    message(FATAL_ERROR "3rdPartyLibs/memAllocators/dlmalloc has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name}
    SOURCES dlmalloc-2.8.4.c winapiMoreCore.cpp allocStep.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude
    PRIVATE_DEFINES ${defines})
endfunction()

dagor_flavors(_dlmalloc)
