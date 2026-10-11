# Ported from prog/gameLibs/dasModules/quirrel/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/modules/dasQuirrel/src
)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()
set(deps 1stPartyLibs/daScript gameLibs/ecs/scripts/das 1stPartyLibs/daScript/modules/dasQuirrel)

dagor_add_library(STRICT
  QUIRREL
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
