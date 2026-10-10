# RapidJSON helpers on EASTL: typed member get/set with error strings, key copies, stringify
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/rapidJsonUtils/include
)
set(sources src/rapidJsonUtils.cpp)
list(APPEND deps 3rdPartyLibs/eastl)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
