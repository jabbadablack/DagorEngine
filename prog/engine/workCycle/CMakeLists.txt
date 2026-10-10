# The work cycle: the main loop, timing, input device init, the console in Dev and Dbg
set(sources
  gameSetts.cpp
  gameActRate.cpp
  gameSceneSelect.cpp
  gameSceneRenderer.cpp
  resetSpentTime.cpp
  workCycle.cpp
  workCyclePerf.cpp
  initVideo.cpp
  initNullJoystick.cpp
  initNullKeyb.cpp
  initNullMouse.cpp
  commonStart.cpp
  mainWndProc.cpp
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources idleCycle.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources initJoystick.cpp initJoystickXInput.cpp initKeybWin.cpp initMouseWin.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources windows/threadedWindow.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources macosx/macIdleCycle.mm initKeybWin.cpp initMouseWin.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "iOS")
  list(APPEND sources macosx/iosIdleCycle.mm initJoystick.cpp initKeybWin.cpp initMouseWin.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "tvOS")
  list(APPEND sources macosx/iosIdleCycle.mm macosx/initRemoteControl.mm initKeybWin.cpp initMouseWin.cpp)
endif()
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND sources idleCycle.cpp initKeybWin.cpp initMouseWin.cpp initJoystickSteam.cpp)
  # the Linux GUI layer comes with engine/osApiWrappers in the programs with DAGOR_LINUX_GUI
endif()
if(DAGOR_PLATFORM STREQUAL "android")
  list(APPEND sources idleCycle.cpp initJoystick.cpp initKeybWin.cpp initMouseWin.cpp)
endif()
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(deps engine/perfMon engine/lowLatency engine/coreUtil)
dagor_use(engine/consoleProc)
list(APPEND deps "$<$<CONFIG:Dev,Dbg>:engine.consoleProc>")
list(APPEND deps engine/drv/vr_device)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
