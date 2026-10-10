# The engine's memory manager. Programs choose its allocator and debug level with the flavor they link (jam's global
# UseMemoryAllocator and UseMemoryDebugLevel): engine/memory[:<allocator>[.<debug level>]]
#   <allocator>    default (dlmalloc on Windows without sanitizers, else rtl), rtl, minrtl, dlmalloc, mimalloc, imported
#   <debug level>  default (off in Rel and IRel), off, min, dbg, dbg2
# e.g. engine/memory, engine/memory:rtl, engine/memory:dlmalloc.dbg, engine/memory:default.off

function(_engine_memory flavor)
  string(REPLACE "." ";" parts "${flavor}")
  list(APPEND parts default default)
  list(GET parts 0 allocator)
  list(GET parts 1 debug)
  if(allocator STREQUAL "")
    set(allocator default)
  endif()
  dagor_check_choice("engine/memory allocator" "${allocator}" default rtl minrtl dlmalloc mimalloc imported)
  dagor_check_choice("engine/memory debug level" "${debug}" default off min dbg dbg2)
  if(allocator STREQUAL "default")
    if(DAGOR_SANITIZE STREQUAL "none" AND DAGOR_PLATFORM STREQUAL "windows")
      set(allocator dlmalloc)
    else()
      set(allocator rtl)
    endif()
  endif()

  set(sources dagmem.cpp mspaceAlloc.cpp framemem.cpp physMem.cpp)
  if(DAGOR_PLATFORM STREQUAL "windows")
    list(APPEND sources dagmem_start.c)
  endif()
  if(debug MATCHES "^(dbg|dbg2)$" AND NOT allocator STREQUAL "imported")
    list(APPEND sources daProfileMem.cpp)
  else()
    list(APPEND sources daProfileMemStub.cpp)
  endif()
  set(defines __B_KERNEL_LIB)
  set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
  set(deps)
  set(source_options)

  if(allocator STREQUAL "rtl")
    list(APPEND defines USE_RTL_ALLOC)
    if(DAGOR_PLATFORM STREQUAL "windows")
      list(APPEND sources msRtlNativeAddr.cpp)
      list(APPEND source_options msRtlNativeAddr.cpp /EHac)
    endif()
  elseif(allocator STREQUAL "minrtl")
    list(APPEND defines USE_RTL_ALLOC)
    set(sources rtlStdMemoryMin/rtlStdMemoryMin.cpp)
  elseif(allocator STREQUAL "dlmalloc")
    list(APPEND defines USE_DLMALLOC)
    list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators)
    if(debug MATCHES "^(dbg|dbg2)$")
      list(APPEND deps 3rdPartyLibs/memAllocators/dlmalloc:debug)
    else()
      list(APPEND deps 3rdPartyLibs/memAllocators/dlmalloc)
    endif()
  elseif(allocator STREQUAL "mimalloc")
    list(APPEND defines USE_MIMALLOC "MI_DEBUG=$<IF:$<CONFIG:Rel,IRel>,0,2>")
    list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators/mimalloc/include
                         ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators/mimalloc/mimalloc/include)
    list(APPEND deps 3rdPartyLibs/memAllocators/mimalloc)
  elseif(allocator STREQUAL "imported")
    list(APPEND defines USE_IMPORTED_ALLOC)
  endif()

  if(debug STREQUAL "default")
    list(APPEND defines "$<$<CONFIG:Rel,IRel>:MEM_DEBUGALLOC=-1>")
  else()
    set(level_off -1)
    set(level_min 0)
    set(level_dbg 1)
    set(level_dbg2 2)
    list(APPEND defines MEM_DEBUGALLOC=${level_${debug}})
  endif()

  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} STRICT
    SOURCES ${sources}
    PRIVATE_INCLUDES ${includes}
    PRIVATE_DEFINES ${defines}
    SOURCE_OPTIONS ${source_options}
    DEPS ${deps})
endfunction()

dagor_flavors(_engine_memory)
