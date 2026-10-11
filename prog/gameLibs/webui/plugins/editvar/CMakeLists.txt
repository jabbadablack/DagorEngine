# Ported from prog/gameLibs/webui/plugins/editvar/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)
set(sources editVarPlugin.cpp)
set(SourceStr editVar.html)
list(APPEND stringify ${SourceStr})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
