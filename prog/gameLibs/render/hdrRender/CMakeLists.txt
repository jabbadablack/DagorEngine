# Ported from prog/gameLibs/render/hdrRender/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources hdrRender.cpp hdrDecoder.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
