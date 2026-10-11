# Ported from prog/gameLibs/quirrel/sqDacoll/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
)
set(sources sqDacoll.cpp)
list(APPEND deps Dagor::Phys)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
