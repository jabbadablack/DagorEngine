# Ported from prog/3rdPartyLibs/codecs/libogg-1.1.3/jamfile (jam2cmake/skeleton.py)
set(includes ../include)
set(sources src/bitwise.c src/framing.c)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
