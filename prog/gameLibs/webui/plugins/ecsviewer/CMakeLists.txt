# Ported from prog/gameLibs/webui/plugins/ecsviewer/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs
  ${DAGOR_PROG_DIR}/dagorInclude
)
set(sources ecsViewerPlugin.cpp ecsViewerPluginListener.cpp)
set(SourceHTML ecsViewer.html)
list(APPEND stringify ${SourceHTML})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
