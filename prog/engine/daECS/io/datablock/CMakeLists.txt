# daECS loading of entities and templates from DataBlock
set(sources dataBlockReader.cpp)
list(APPEND deps engine/daECS/utility)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps engine/ioSys)
endif()

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
