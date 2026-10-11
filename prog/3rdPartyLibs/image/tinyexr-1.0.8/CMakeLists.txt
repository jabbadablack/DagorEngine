# Ported from prog/3rdPartyLibs/image/tinyexr-1.0.8/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng)
set(sources tinyexr.cc)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
