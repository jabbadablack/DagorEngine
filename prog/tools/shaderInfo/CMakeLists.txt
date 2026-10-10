# shaderInfo: inspects shader dumps (variables, blocks, bytecode disassembly; AMD's Radeon GPU Analyzer statistics when
# RDTS_ROOT points to a Radeon Developer Tool Suite)
list(APPEND defines SET_DEFAULT_MAX_SHVARS=8192)
set(includes
  ${DAGOR_PROG_DIR}/engine/shaders
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/tools/ShaderCompiler2/shaderBlobDisassembler/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  ${DAGOR_PROG_DIR}/tools/sharedInclude
)
set(sources shaderInfo.cpp rga.cpp rgaPipelineState.cpp main.cpp)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/lib3d
  engine/drv/drv3d_null
  engine/drv/shadersMetaData
  gameLibs/shaderBlobUnpack
  3rdPartyLibs/eastl
  3rdPartyLibs/hash/BLAKE3
  engine/shaders
  engine/perfMon/daProfilerStub
  tools/ShaderCompiler2/shaderBlobDisassembler
  tools/libTools/util
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()
set(libs)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs d3dcompiler)
endif()

dagor_add_executable(shaderInfo CONSOLE
  CDK
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
