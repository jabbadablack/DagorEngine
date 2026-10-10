# netImgui (remote ImGui) for the engine's ImGui libraries, outside Rel (jam's addNetImgui.jam): sets
# NET_IMGUI_DEFINES, NET_IMGUI_INCLUDES and NET_IMGUI_DEPS
set(NET_IMGUI_DEFINES)
set(NET_IMGUI_INCLUDES)
set(NET_IMGUI_DEPS)
if(DAGOR_NET_IMGUI AND DAGOR_PLATFORM MATCHES "^(windows|linux|macOS|android|iOS)$")
  set(NET_IMGUI_DEFINES "$<$<NOT:$<CONFIG:Rel>>:ADD_NET_IMGUI>")
  set(NET_IMGUI_INCLUDES ${DAGOR_PROG_DIR}/3rdPartyLibs/netImgui ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5)
  dagor_use(3rdPartyLibs/netImgui 3rdPartyLibs/arc/zstd-1.4.5)
  set(NET_IMGUI_DEPS "$<$<NOT:$<CONFIG:Rel>>:3rdPartyLibs.netImgui>" "$<$<NOT:$<CONFIG:Rel>>:3rdPartyLibs.arc.zstd-1.4.5>")
endif()
