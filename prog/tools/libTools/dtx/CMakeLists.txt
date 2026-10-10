# Tools texture library: DDS conversion and saving (on nvtt 2.0.7), DDSx plugins, texture names, RGBE images
set(sources
  dtxConvertImage.cpp
  dtxConvertFile.cpp
  rgbe.cpp
  dtxSave.cpp
  dtxSampler.cpp
  de_TextureName.cpp
  de_TexNameMkRel.cpp
  ddsxPlugin.cpp
  ddsInfo.cpp
)
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/nvtt-2.0.7
  ${DAGOR_PROG_DIR}/tools/sharedInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
)
set(deps engine/image 3rdPartyLibs/convert/nvtt-2.0.7 3rdPartyLibs/image/jpeg-6b 3rdPartyLibs/image/avif)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  list(APPEND deps 3rdPartyLibs/arc/lzma-9.20)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
