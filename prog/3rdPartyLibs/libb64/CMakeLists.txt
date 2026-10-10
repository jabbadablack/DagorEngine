# libb64 base64 encoder/decoder
set(includes include)
set(sources src/cdecode.c src/cencode.c)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
