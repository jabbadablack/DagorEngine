# Ported from prog/engine/drv/hid_gamepad_xinput/jamfile (jam2cmake/skeleton.py)
set(sources gamepad_classdrv.cpp gamepad_device.cpp gamepad_create.cpp mouse_emu.cpp)
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  set(deps engine/baseUtil)
endif()
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
