# Copying Quirrel values and calls between two Quirrel VMs
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/engine/sharedInclude
)
set(sources sqCrossCall.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes})
