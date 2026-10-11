# Ported from prog/engine/screenShotSystem/jamfile (jam2cmake/skeleton.py)
set(sources screenShotSystem.cpp)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
