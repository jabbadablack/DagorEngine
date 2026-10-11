# Ported from prog/gameLibs/profileEventsGUI/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND deps 3rdPartyLibs/eastl)
set(sources profileEventsGUI.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
