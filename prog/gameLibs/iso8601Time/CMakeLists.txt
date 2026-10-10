# ISO 8601 time parsing and formatting
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources iso8601Time.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options})
