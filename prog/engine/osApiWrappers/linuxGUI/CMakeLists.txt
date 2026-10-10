# The Linux GUI layer (window title, clipboard, event loop) on X11 and Wayland, for programs with DAGOR_LINUX_GUI
if(NOT DAGOR_PLATFORM STREQUAL "linux")
  return()
endif()
if(NOT DAGOR_LINUX_X11 AND NOT DAGOR_LINUX_WAYLAND)
  message(FATAL_ERROR "DAGOR_LINUX_X11 or DAGOR_LINUX_WAYLAND must be on")
endif()
set(sources mux.cpp linuxSetTitle.cpp linuxClipboard.cpp)
set(defines)
set(deps)
set(libs xkbcommon)
if(DAGOR_LINUX_WAYLAND)
  list(APPEND sources wayland.cpp wayland_loader.cpp)
  list(APPEND defines USE_WAYLAND)
  list(APPEND deps 3rdPartyLibs/wayland)
endif()
if(DAGOR_LINUX_X11)
  list(APPEND sources x11.cpp)
  list(APPEND defines USE_X11)
  list(APPEND libs X11 Xcursor)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude
  PRIVATE_DEFINES ${defines}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
