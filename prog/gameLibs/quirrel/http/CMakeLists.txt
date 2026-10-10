# Quirrel bindings of the async HTTP client (responses by callback or through the event bus)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
)
set(deps gameLibs/quirrel/quirrel_json gameLibs/quirrel/sqEventBus 1stPartyLibs/jsoncpp)
set(sources sqHttpClient.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
