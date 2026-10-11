# Ported from prog/gameLibs/webui/plugins/colorpicker/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources colorpicker.cpp)
set(SourceJS colorGradient.js colorPicker.js cookie.js)
set(deps gameLibs/colorPipette)
list(APPEND stringify ${SourceJS})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} STRINGIFY ${stringify})
