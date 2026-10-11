# Ported from prog/gameLibs/daEditorE/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/tools/sharedInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
)
set(sources daEditorE.cpp daEditorE_sq.cpp de_object.cpp de_objEditor.cpp gizmofilter.cpp)
set(deps tools/libTools/util gameLibs/quirrel/sqEventBus gameLibs/quirrel/frp gameLibs/quirrel/quirrel_json)

dagor_add_library(QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
