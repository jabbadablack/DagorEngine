# Ported from prog/gameLibs/ecs/scripts/dasSq/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
list(APPEND deps
  gameLibs/quirrel/quirrel_json
  gameLibs/ecs/scripts/sq
  gameLibs/ecs/scripts/das
  gameLibs/quirrel/bindQuirrelEx
)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
