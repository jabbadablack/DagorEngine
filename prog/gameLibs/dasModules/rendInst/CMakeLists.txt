# Ported from prog/gameLibs/dasModules/rendInst/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
set(SourceDAS rendInst.das)
list(APPEND stringify ${SourceDAS})
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()
list(APPEND deps 1stPartyLibs/daScript gameLibs/ecs/scripts/das)
list(APPEND deps Dagor::Phys)

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  STRINGIFY ${stringify}
)
