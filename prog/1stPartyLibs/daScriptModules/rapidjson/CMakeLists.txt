dagor_add_library(
  SOURCES jsonWriter.cpp rapidjson.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
    ${DAGOR_PROG_DIR}/1stPartyLibs/rapidJsonUtils/include
    ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  LICENSE_FILES ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson
)
