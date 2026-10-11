# Ported from prog/3rdPartyLibs/codecs/libtheora-1.0/jamfile (jam2cmake/skeleton.py): the decoder (no program builds the
# encoder, jam's IncludeEncoder)
set(includes ../include)
set(dec_src
  apiwrapper.c
  bitpack.c
  decapiwrapper.c
  decinfo.c
  decode.c
  dequant.c
  fragment.c
  huffdec.c
  idct.c
  info.c
  internal.c
  quant.c
  state.c
)
list(TRANSFORM dec_src PREPEND lib/dec/)
set(sources ${dec_src} lib/enc/encoder_disabled.c)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND c_options /wd4554)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND c_options -Wno-logical-op-parentheses -Wno-parentheses -Wno-tautological-compare)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl|gcc)$")
  list(APPEND options -Wno-unused-parameter)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options} C_OPTIONS ${c_options})
