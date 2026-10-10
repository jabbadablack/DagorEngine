# The reference providers of daBuild (plugins): the assets referenced by composites, effects and splines
include(../dabuildPlugin.cmake)
foreach(provider composit efx spline)
  dabuild_plugin(${provider}RefProv
    SOURCES ${provider}RefProv.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/tools/sceneTools/daEditorX/include
    DEPS engine/startup tools/libTools/assetMgr)
endforeach()
