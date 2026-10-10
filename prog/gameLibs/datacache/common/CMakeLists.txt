# Data cache: shared tracing
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude)
set(sources trace.cpp)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps engine/kernel)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
