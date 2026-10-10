# Microsoft's mimalloc, an allocator of engine/memory (engine/memory:mimalloc). Its own checks (MI_DEBUG 2) are on in
# Dev and Dbg; flavor nodebug has none (for engine/memory:mimalloc.off).
function(_mimalloc flavor)
  if(flavor STREQUAL "nodebug")
    set(debug 0)
  elseif(flavor)
    message(FATAL_ERROR "3rdPartyLibs/memAllocators/mimalloc has no flavor '${flavor}'")
  else()
    set(debug "$<IF:$<CONFIG:Rel,IRel>,0,2>")
  endif()
  set(sources src/alloc.c src/alloc-aligned.c src/alloc-posix.c src/arena.c src/bitmap.c src/heap.c src/init.c
    src/libc.c src/options.c src/os.c src/page.c src/random.c src/segment.c src/segment-map.c src/stats.c)
  set(options)
  set(libs)
  if(DAGOR_PLATFORM STREQUAL "windows")
    list(APPEND sources src/prim/windows/prim.c)
    set(libs advapi32)
    if(DAGOR_MSVC_LIKE)
      set(options -wd4055 -wd4054)
    endif()
  else()
    list(APPEND sources src/prim/unix/prim.c)
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name}
    SOURCES ${sources}
    PRIVATE_INCLUDES include mimalloc/include
    PRIVATE_DEFINES MI_DEBUG=${debug}
    COMPILE_OPTIONS ${options}
    SYSTEM_LIBS ${libs}
  )
endfunction()

dagor_flavors(_mimalloc)
