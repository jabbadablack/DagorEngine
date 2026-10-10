# daKernel, the shared engine kernel of the tools of the editor tree (DAGOR_KERNEL_LINKAGE dynamic): the OS wrappers,
# kernel, memory manager (on the C runtime's allocator), I/O, base utilities, profiler and EASTL, exported to the
# tools and their plugins, which import them instead of linking their own copies
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory:rtl
  engine/ioSys
  engine/baseUtil
  engine/perfMon
  engine/perfMon/daProfiler
  3rdPartyLibs/eastl:kernel
)
set(options)
set(libs)
set(link_options)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND deps engine/osApiWrappers/messageBox)
  set(libs dbghelp user32)
elseif(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub engine/workCycle/stub)
  set(libs dl pthread rt m stdc++)
  set(link_options -Wl,--no-undefined)
  # only what the kernel exports (KRNLIMP) is visible outside the library
  set(options -fvisibility=hidden)
endif()

dagor_add_shared_library(tools.libTools.daKernel STRICT CDK OUTPUT_NAME daKernel
  SOURCES daKernel.cpp namedPtr.cpp gpFuncTable.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude
  PRIVATE_DEFINES __B_KERNEL_LIB
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
  LINK_OPTIONS ${link_options}
)
