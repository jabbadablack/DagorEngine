# Intel's ISPC Texture Compressor (BC1-7, ETC1, ASTC) with its ISPC kernels for several instruction sets (the best one
# is picked at run time); GameTechDev/ISPCTextureCompressor rev 691513b4. The kernels' headers are generated into the
# build dir (CMake's default place: a set ISPC_HEADER_DIRECTORY loses its leading / in Ninja's dependencies on Linux).
set(isa)
if(DAGOR_ARCH STREQUAL "x86_64")
  set(isa sse2 sse4 avx avx2)
elseif(DAGOR_ARCH STREQUAL "arm64")
  set(isa neon)
else()
  message(FATAL_ERROR "3rdPartyLibs/convert/ispc_texcomp has no ISPC targets for ${DAGOR_ARCH}")
endif()
dagor_add_library(
  SOURCES ispc_texcomp.cpp ispc_texcomp_astc.cpp kernel.ispc kernel_astc.ispc
  PRIVATE_INCLUDES ${CMAKE_CURRENT_BINARY_DIR} # where CMake writes the kernels' headers
  COMPILE_OPTIONS "$<$<COMPILE_LANGUAGE:ISPC>:-O2;--pic;--opt=fast-math;--woff>"
  LICENSE_FILES license.txt
)
set_property(TARGET 3rdPartyLibs.convert.ispc_texcomp PROPERTY ISPC_INSTRUCTION_SETS ${isa})
