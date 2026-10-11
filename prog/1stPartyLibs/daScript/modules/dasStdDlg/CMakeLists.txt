# daScript's standard dialogs (open/save file, message boxes) on the platform's API (replaces the upstream
# CMakeLists.txt of daScript's own build)
set(sources src/dasStdDlg.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources src/dasStdDlgWin.cpp)
elseif(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND sources src/dasStdDlgGtk.cpp)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources src/dasStdDlgOsx.mm)
else()
  list(APPEND sources src/dasStdDlgNotImplemented.cpp)
endif()
dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  DEPS 1stPartyLibs/daScript
)
