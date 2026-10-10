# NVIDIA Texture Tools 2.0.7: DXT compression (with squish), image filtering, normal maps and DDS I/O
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/nvtt-2.0.7 ${DAGOR_PROG_DIR}/3rdPartyLibs/image/jpeg-6b)
set(sources
  nvcore/debug.cpp
  nvcore/library.cpp
  nvcore/strLib.cpp
  nvcore/textReader.cpp
  nvcore/textWriter.cpp
  nvimage/blockDXT.cpp
  nvimage/colorBlock.cpp
  nvimage/directDrawSurface.cpp
  nvimage/filter.cpp
  nvimage/floatImage.cpp
  nvimage/image.cpp
  nvimage/imageIO.cpp
  nvimage/normalMap.cpp
  nvimage/quantize.cpp
  nvmath/plane.cpp
  nvtt/compressDXT.cpp
  nvtt/compressionOptions.cpp
  nvtt/compressor.cpp
  nvtt/compressRGB.cpp
  nvtt/inputOptions.cpp
  nvtt/nvtt.cpp
  nvtt/nvtt_wrapper.cpp
  nvtt/optimalCompressDXT.cpp
  nvtt/outputOptions.cpp
  nvtt/quickCompressDXT.cpp
  nvtt/cuda/cudaCompressDXT.cpp
  nvtt/cuda/cudaUtils.cpp
  nvtt/squish/clusterfit.cpp
  nvtt/squish/colourblock.cpp
  nvtt/squish/colourfit.cpp
  nvtt/squish/colourset.cpp
  nvtt/squish/fastclusterfit.cpp
  nvtt/squish/maths.cpp
  nvtt/squish/weightedclusterfit.cpp
  nvtt/squish/singlecolourfit.cpp
  nvtt/squish/squish.cpp
  nvtt/squish/alpha.cpp
  nvtt/squish/rangefit.cpp
)
set(defines NVTT_EXPORTS)
if(DAGOR_ARCH MATCHES "^(e2k|x86_64)$")
  list(APPEND defines __SSE2__ __SSE__ __MMX__)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND defines WIN32 _WINDOWS _USRDLL)
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND defines SQUISH_USE_ALTIVEC=0)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines})
