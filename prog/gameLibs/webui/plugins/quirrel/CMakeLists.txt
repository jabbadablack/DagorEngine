# Ported from prog/gameLibs/webui/plugins/quirrel/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/dagorInclude
)
set(sources sqDebuggerPlugin.cpp)
set(SourceStr quirrelDebugger.html)
list(APPEND stringify ${SourceStr})

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
