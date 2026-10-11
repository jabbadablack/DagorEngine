# Ported from prog/gameLibs/dasModules/stdGui/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
set(SourceDAS )
list(APPEND stringify ${SourceDAS})
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()
set(deps 1stPartyLibs/daScript)
if(DAGOR_DAS_AOT_COMPILER)
  list(APPEND defines DAS_AOT_COMPILER) # the AOT compiler's stubs (prog/gameLibs/dasModules/module_common.jam)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  STRINGIFY ${stringify}
)
