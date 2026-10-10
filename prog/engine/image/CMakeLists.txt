# Image loading/saving (TGA, JPEG, PSD, PNG, AVIF, TIFF, EXR, DDS, SVG), resampling and DXT compression
set(sources
  loadTga.cpp
  saveTga.cpp
  loadJpeg.cpp
  saveJpeg.cpp
  jpgCommon.cpp
  jpgRead.cpp
  jpgWrite.cpp
  loadPsd.cpp
  loadPng.cpp
  loadAvif.cpp
  savePng.cpp
  loadTiff.cpp
  saveTiff.cpp
  saveExr.cpp
  loadImage.cpp
  loadDds.cpp
  loadDdsTex.cpp
  imgAlloc.cpp
  resampleImage.cpp
  imageCompare.cpp
  regImageLoadAny.cpp
  regImageLoadJpeg.cpp
  regImageLoadPsd.cpp
  regImageLoadTga.cpp
  regImageLoadTiff.cpp
  regImageLoadPng.cpp
  regImageLoadSvg.cpp
  regImageLoadAvif.cpp
  dxtCompress.cpp
)
set(options)
if(DAGOR_CC STREQUAL "gcc")
  list(APPEND options -Wno-uninitialized) # false positives of gcc 11
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
    ${DAGOR_PROG_DIR}/3rdPartyLibs/binPack2D/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/image/avif/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/fastDXT
  COMPILE_OPTIONS ${options}
  DEPS
    3rdPartyLibs/convert/fastDXT
    3rdPartyLibs/image/jpeg-6b
    3rdPartyLibs/image/libpng-1.4.22
    3rdPartyLibs/image/imageresampler
  LICENSE_FILES ${DAGOR_PROG_DIR}/3rdPartyLibs/nanosvg
)
