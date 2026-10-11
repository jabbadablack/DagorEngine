# Ported from prog/1stPartyLibs/daScript/modules/dasQuirrel/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel)
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND options -Wno-deprecated-declarations)
endif()
set(AllSrcFolder_CPP src)
dagor_glob_sources(sources DIRS ${AllSrcFolder_CPP} GLOB *.cpp)
list(APPEND deps 3rdPartyLibs/eastl 1stPartyLibs/daScript)

dagor_add_library(STRICT
  QUIRREL
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
