# Ported from prog/gameLibs/webui/websocket/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/dagorInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
)
set(sources webSocketStream.cpp)
set(deps 3rdPartyLibs/mongoose)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
