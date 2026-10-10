# daScript modules of the engine: files, DataBlock, console, math, debug drawing
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
set(SourceDAS dagorFiles.das dagorDataBlock.das dagorConsole.das dagorMath.das dagorDebug3d.das)
list(APPEND stringify ${SourceDAS})
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()
set(deps 1stPartyLibs/daScript 3rdPartyLibs/arc/zstd-1.4.5)

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  STRINGIFY ${stringify}
)
