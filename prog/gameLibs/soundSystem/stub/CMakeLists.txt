# Ported from prog/gameLibs/soundSystem/stub/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources soundSystemStub.cpp debugStub.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
