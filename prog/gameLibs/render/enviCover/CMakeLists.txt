# Ported from prog/gameLibs/render/enviCover/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources enviCover.cpp enviCoverVars.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
