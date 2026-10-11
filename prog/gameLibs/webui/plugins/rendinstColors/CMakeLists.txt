# Ported from prog/gameLibs/webui/plugins/rendinstColors/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)
set(sources rendinstColorsPlugin.cpp)
set(SourceHTML rendinstColors.html)
list(APPEND stringify ${SourceHTML})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} STRINGIFY ${stringify})
