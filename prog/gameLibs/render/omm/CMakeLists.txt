# Opacity micromaps for ray tracing baked with NVIDIA's OMM SDK (Windows and Linux x86_64; a stub elsewhere)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/omm_sdk/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/omm_sdk/src
  ${DAGOR_PROG_DIR}/3rdPartyLibs/omm_sdk/shaders
  ${DAGOR_PROG_DIR}/3rdPartyLibs/stb
  ${DAGOR_PROG_DIR}/3rdPartyLibs/hash
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/lz4
)
if("${DAGOR_PLATFORM}-${DAGOR_ARCH}" MATCHES "^(linux\-x86_64|windows\-x86_64)$")
  set(sources
    omm.cpp
    omm_cpu.cpp
    omm_debug.cpp
    ../../../3rdPartyLibs/omm_sdk/src/bake.cpp
    ../../../3rdPartyLibs/omm_sdk/src/bake_cpu_impl.cpp
    ../../../3rdPartyLibs/omm_sdk/src/bake_gpu_impl.cpp
    omm_sdk_debug_stub.cpp
    ../../../3rdPartyLibs/omm_sdk/src/serialize_impl.cpp
    ../../../3rdPartyLibs/omm_sdk/src/shader_bindings.cpp
    ../../../3rdPartyLibs/omm_sdk/src/texture_impl.cpp
  )
else()
  set(sources omm_stub.cpp)
endif()
list(APPEND deps engine/lib3d engine/shaders 3rdPartyLibs/eastl 3rdPartyLibs/hash 3rdPartyLibs/arc/lz4)
list(APPEND defines
  GLM_ENABLE_EXPERIMENTAL
  OMM_VK_S_SHIFT=0
  OMM_VK_T_SHIFT=128
  OMM_VK_B_SHIFT=256
  OMM_VK_U_SHIFT=384
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /Zc:__cplusplus)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  # a function-style macro: CMake's COMPILE_DEFINITIONS cannot hold those
  list(APPEND options "-DOMM_DEPRECATED_MSG(X)=" -Wno-ignored-attributes)
  if("${DAGOR_PLATFORM}-${DAGOR_ARCH}" STREQUAL "linux-x86_64")
    list(APPEND options -Wno-switch)
  endif()
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
