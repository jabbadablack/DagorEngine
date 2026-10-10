# The vehicle exporter of daBuild (a plugin): the vehicle physics assets
include(${DAGOR_PROG_DIR}/tools/sceneTools/assetExp/dabuildPlugin.cmake)
dabuild_plugin(vehicleExp
  SOURCES vehicleExp.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  DEPS engine/startup engine/math tools/libTools/assetMgr)
