# VR device interface: a stub in the programs without VR. The programs with VR set the DAGOR_VR target property and
# get engine.drv.vr_device.vr (OpenXR, with the emulator in Dev and Dbg), see dagor_add_link_choice().
dagor_add_library(engine.drv.vr_device.stub SOURCES vrDeviceStub.cpp)
dagor_add_link_choice(engine.drv.vr_device PROPERTY DAGOR_VR ON engine.drv.vr_device.vr OFF engine.drv.vr_device.stub)
