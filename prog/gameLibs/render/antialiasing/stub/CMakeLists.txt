# Ported from prog/gameLibs/render/antialiasing/stub/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources antialiasingStub.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
