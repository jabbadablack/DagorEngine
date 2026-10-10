# Public domain bencode (the BitTorrent encoding) decoder
set(includes ${CMAKE_CURRENT_SOURCE_DIR})
set(sources bencode.c)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND c_options -Dstrtoll=_strtoi64)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} C_OPTIONS ${c_options})
