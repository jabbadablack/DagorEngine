# daEditorX bitmask image manager service (IBitMaskImageMgr) on libtiff
set(includes ${DAGOR_PROG_DIR}/tools/sceneTools/daEditorX/include ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources bitMaskMgr.cpp)
set(deps 3rdPartyLibs/image/tiff-4.4.0)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
