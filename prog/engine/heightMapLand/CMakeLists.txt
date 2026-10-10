# Compressed heightmaps: block (min plus delta) compression of 16-bit heights and their decoding
set(sources compressedHeightmap.cpp)

dagor_add_library(SOURCES ${sources})
