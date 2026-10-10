# Quirrel bindings of the Windows registry (value reads and writes)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel)
set(sources win_registry.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes})
