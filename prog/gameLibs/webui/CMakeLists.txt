# webui: the programs' HTTP server for the browser tools, with its plugins
set(plugins colorpicker dagor dargMcp editvar grapheditor profiler screenshot shadervars quirrel)
if(DAGOR_PLATFORM STREQUAL "tvOS")
  list(APPEND plugins tvOS)
endif()
list(TRANSFORM plugins PREPEND gameLibs/webui/plugins/)

dagor_add_library(STRICT
  SOURCES httpserver.cpp bson.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/dagorInclude
    ${DAGOR_PROG_DIR}/engine/sharedInclude # for access to the shaders' implementation
  DEPS ${plugins}
  STRINGIFY webuiIndexTemplate.html
)
