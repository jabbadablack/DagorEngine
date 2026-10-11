# Ported from prog/gameLibs/webui/plugins/grapheditor/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)
set(sources graphEditorPlugin.cpp)
set(SourceStr stubNodesSettings.js)
set(SourceArray graphEditor.html)
list(APPEND stringify ${SourceStr})
list(APPEND stringify_array ${SourceArray})

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  STRINGIFY ${stringify}
  STRINGIFY_ARRAY ${stringify_array}
)
