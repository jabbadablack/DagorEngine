# DXIL shader compilation through DXC (dxcompiler loaded at run time) and compiled shader header generation
set(sources compiler_dxc.cpp shader_header_compiler.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
