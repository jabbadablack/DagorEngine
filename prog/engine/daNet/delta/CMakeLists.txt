# daNet delta compression (RLE, history buffers)
set(sources rle.cpp history.cpp buffer.cpp deltaCompression.cpp)
list(APPEND deps engine/daNet)

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
