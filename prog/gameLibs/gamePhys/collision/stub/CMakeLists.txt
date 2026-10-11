# Ported from prog/gameLibs/gamePhys/collision/stub/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources collisionStub.cpp)
list(APPEND deps Dagor::Phys)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
