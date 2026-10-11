# Ported from prog/engine/drv/hid_joystick/jamfile (jam2cmake/skeleton.py)
set(sources
  joy_classdrv.cpp
  joy_device.cpp
  joy_ff_effects.cpp
  joy_enumdev.cpp
  joy_create.cpp
  joy_composite.cpp
)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
