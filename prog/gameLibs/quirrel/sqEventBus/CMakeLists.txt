# Quirrel event bus: events between VMs and native code, the eventbus module
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
)
set(deps gameLibs/quirrel/sqCrossCall)
set(sources sqEventBus.cpp bind.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
