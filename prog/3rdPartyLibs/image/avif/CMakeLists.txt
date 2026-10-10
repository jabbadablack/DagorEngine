# libavif 0.11.1: the AV1 Image File Format, with dav1d as its only codec (decoding)
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/image/avif)
set(sources
  src/alpha.c
  src/avif.c
  src/codec_dav1d.c
  src/colr.c
  src/diag.c
  src/exif.c
  src/io.c
  src/mem.c
  src/obu.c
  src/rawdata.c
  src/read.c
  src/reformat.c
  src/reformat_libsharpyuv.c
  src/reformat_libyuv.c
  src/scale.c
  src/stream.c
  src/utils.c
  src/write.c
)
list(APPEND deps 3rdPartyLibs/codecs/dav1d)
set(includes include ${DAGOR_PROG_DIR}/3rdPartyLibs/codecs/dav1d/include)
set(defines AVIF_CODEC_DAV1D)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
