# Ported from prog/gameLibs/webui/plugins/dargMcp/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/dagorInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
)
set(deps 3rdPartyLibs/image/libpng-1.4.22)
set(sources dargMcpPlugin.cpp)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
