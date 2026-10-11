# Ported from prog/gameLibs/aviWriter/jamfile (jam2cmake/skeleton.py)
set(sources aviWriter.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
