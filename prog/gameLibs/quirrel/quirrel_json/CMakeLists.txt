# JSON for Quirrel: conversion to and from jsoncpp and rapidjson, a direct JSON parser and writer
set(sources
  quirrel_json.cpp
  rapidjson.cpp
  jsoncpp.cpp
  direct_json/direct_json_parse.cpp
  direct_json/direct_json_write.cpp
)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
)
set(deps 1stPartyLibs/jsoncpp 3rdPartyLibs/arc/zstd-1.4.5)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
