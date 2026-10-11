# Ported from prog/gameLibs/vr/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources vrGuiSurface.cpp vrHands.cpp)
list(APPEND deps Dagor::Phys)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
