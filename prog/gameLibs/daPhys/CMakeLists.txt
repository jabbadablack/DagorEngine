# Ported from prog/gameLibs/daPhys/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources particlePhys.cpp)
set(deps 3rdPartyLibs/regExp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
