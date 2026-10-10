# ImGui helpers: BLK editing, strings, images, a filtered combo box
include(../netImgui.cmake)
dagor_add_library(
  SOURCES imguiBlk.cpp imguiMisc.cpp imguiString.cpp imguiImage.cpp imguiComboWithFilter.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude ${NET_IMGUI_INCLUDES}
  PRIVATE_DEFINES ${NET_IMGUI_DEFINES}
  DEPS 3rdPartyLibs/imgui ${NET_IMGUI_DEPS}
)
