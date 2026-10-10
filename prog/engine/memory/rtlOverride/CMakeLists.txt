# The C runtime's allocator for the programs and libraries on daKernel (the memory manager is in daKernel)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  message(FATAL_ERROR "engine/memory/rtlOverride is for the trees on daKernel (DAGOR_KERNEL_LINKAGE dynamic)")
endif()
dagor_add_library(SOURCES stubRtl.cpp PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/3rdPartyLibs/memAllocators
  PRIVATE_DEFINES USE_RTL_ALLOC)
