# Ported from prog/gameLibs/webui/plugins/editorCurves/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)
set(sources curveEditorJsPlugin.cpp)
set(SourceJS curveEditor.js)
list(APPEND stringify ${SourceJS})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
