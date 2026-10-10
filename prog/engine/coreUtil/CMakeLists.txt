# Core utilities: simple parameter blocks, base64, localization tables, fly mode
set(sources simplePBlock.cpp base64.cpp localization.cpp)
if(NOT DAGOR_PLATFORM STREQUAL "android" OR TRUE)
  list(APPEND sources flyMode.cpp)
endif()
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(deps 3rdPartyLibs/eastl)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
