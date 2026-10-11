# Ported from prog/gameLibs/dasModules/generic/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/rapidJsonUtils/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
set(SourceDAS animchar.das zones.das dagorFindFiles.das grid.das)
list(APPEND stringify ${SourceDAS})
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
  list(APPEND defines "$<$<NOT:$<CONFIG:Rel>>:ANIM_PBC_HOT_RELOAD_ENABLED>") # jam had it on Windows only
endif()
set(deps 1stPartyLibs/daScript gameLibs/gameMath)
list(APPEND deps Dagor::Phys)

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  STRINGIFY ${stringify}
)
