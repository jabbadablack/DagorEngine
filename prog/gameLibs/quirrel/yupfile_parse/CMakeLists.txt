# Quirrel module reading .yup files (through yup_parse)
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/yup_parse
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel/yupfile_parse
)
set(sources yupfile_parse.cpp)
set(deps engine/coreUtil)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()

dagor_add_library(STRICT
  QUIRREL
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
