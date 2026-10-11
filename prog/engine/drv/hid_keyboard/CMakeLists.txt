# Ported from prog/engine/drv/hid_keyboard/jamfile (jam2cmake/skeleton.py)
set(sources kbd_shifts.cpp kbd_device_common.cpp kbd_globals.cpp kbd_classdrv_win.cpp kbd_device_win.cpp)
if(DAGOR_PLATFORM STREQUAL "linux")
  set(libs X11)
endif()
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} SYSTEM_LIBS ${libs})
