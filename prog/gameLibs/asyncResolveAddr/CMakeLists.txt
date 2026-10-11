# Ported from prog/gameLibs/asyncResolveAddr/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources asyncResolveAddr.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
