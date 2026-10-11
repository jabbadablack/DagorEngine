# Ported from prog/gameLibs/webui/plugins/shadervars/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/webui
  ${DAGOR_PROG_DIR}/dagorInclude
)
set(sources shaderPlugin.cpp)
list(APPEND stringify shaderVars.html)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
