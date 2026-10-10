# The disassembler of compiled shader blobs (SPIR-V through spirv-tools, DXIL on Windows), for shaderInfo and the
# shader compilers' debug output
set(sources disasm.cpp debugSpitfile.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(deps 3rdPartyLibs/regExp 3rdPartyLibs/vulkan/spirv-tools gameLibs/shaderBlobUnpack)
if(DAGOR_PLATFORM MATCHES "^(linux|macOS|windows)$")
  list(APPEND includes
    ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/vulkan/spirv-tools/include
  )
  if(DAGOR_PLATFORM STREQUAL "windows")
    list(APPEND deps gameLibs/dxil)
  endif()
else()
  message(FATAL_ERROR "tools/ShaderCompiler2/shaderBlobDisassembler does not support ${DAGOR_PLATFORM}")
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
