# LZMA SDK 9.20 encoder and decoder
set(sources LzmaDec.c LzmaEnc.c LzFind.c)
set(c_options -D_7ZIP_ST -D__B_KERNEL_LIB)

dagor_add_library(SOURCES ${sources} C_OPTIONS ${c_options})
