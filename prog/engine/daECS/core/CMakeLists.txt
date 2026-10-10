# daECS: entities, components, templates, systems, events
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  set(deps engine/baseUtil)
endif()
list(APPEND deps 3rdPartyLibs/eastl 3rdPartyLibs/regExp)

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
