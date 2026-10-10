# detex: BCn/ETC texture decompression
set(sources
  bits.c
  bptc-tables.c
  clamp.c
  convert.c
  dds.c
  decompress-bc.c
  decompress-bptc-float.c
  decompress-bptc.c
  decompress-eac.c
  decompress-etc.c
  decompress-rgtc.c
  division-tables.c
  ktx.c
  raw.c
  texture.c
)
if(DAGOR_CC MATCHES "^(clang|clang\-cl|gcc)$")
  list(APPEND c_options -Wno-unused-parameter)
endif()

dagor_add_library(SOURCES ${sources} C_OPTIONS ${c_options})
