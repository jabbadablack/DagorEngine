# Quirrel base64 encoding and decoding module
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel)
set(deps gameLibs/quirrel/quirrel_json)
set(sources base64.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
