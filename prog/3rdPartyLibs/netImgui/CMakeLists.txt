# netImgui: ImGui drawn remotely over the network
set(includes
  ${CMAKE_CURRENT_SOURCE_DIR}
  nlohmann_json
  quicklz
  ${DAGOR_PROG_DIR}/3rdPartyLibs/imgui
  ${DAGOR_PROG_DIR}/3rdPartyLibs/stb
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5
)
set(sources
  source/NetImgui_Api.cpp
  source/NetImgui_Client.cpp
  source/NetImgui_CmdPackets_DrawFrame.cpp
  quicklz/quicklz.cpp
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources source/NetImgui_NetworkWin32.cpp)
  list(APPEND defines NETIMGUI_WINSOCKET_ENABLED)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|linux|macOS)$")
  list(APPEND sources source/NetImgui_NetworkPosix.cpp)
  list(APPEND defines NETIMGUI_POSIX_SOCKETS_ENABLED)
endif()
set(deps 3rdPartyLibs/imgui 3rdPartyLibs/arc/zstd-1.4.5)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
