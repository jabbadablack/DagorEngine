# SPIR-V tooling of the shader compilers: compiling HLSL with DXC and the passes that fix up its SPIR-V for the engine
list(APPEND sources
  traits_table.cpp
  module_writer.cpp
  module_reader.cpp
  module_builder.cpp
  atomic_counter_resolve_pass.cpp
  compile_header_pass.cpp
  buffer_unique_pointer_pass.cpp
  dxc_bugfix_pass.cpp
  rename_entry_points_pass.cpp
  semantic_resolve_pass.cpp
  structure_layout_validation_pass.cpp
  reflection_cleanup_pass.cpp
  compiler_dxc.cpp
)
list(APPEND includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/spirv-tools/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
dagor_require_sdk(dxc)
list(APPEND deps 3rdPartyLibs/vulkan/spirv-tools sdk::dxc)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs Ole32)
endif()
set(defines _CROSS_TARGET_SPIRV)
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND options -Wno-switch -Wno-ambiguous-reversed-operator -Wno-deprecated-declarations)
endif()
if(DAGOR_PLATFORM STREQUAL "linux" AND DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND defines __EMULATE_UUID)
  list(APPEND options
    -Wno-sometimes-uninitialized
    -Wno-switch
    -Wno-ambiguous-reversed-operator
    -Wno-deprecated-declarations
  )
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
