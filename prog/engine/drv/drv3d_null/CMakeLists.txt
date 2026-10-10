# The null 3d driver: the driver interface doing nothing at all (command-line tools that only need the API). In trees
# with the multi-driver interface it is one of its drivers, so it has to be in DAGOR_D3D_DRIVERS there.
if(DAGOR_D3D_MULTI)
  if(NOT "null" IN_LIST DAGOR_D3D_DRIVERS)
    message(FATAL_ERROR "engine/drv/drv3d_null in a multi-driver tree needs null in DAGOR_D3D_DRIVERS")
  endif()
  set(sources d3d_stub_m.cpp)
else()
  set(sources d3d_stub.cpp)
endif()
dagor_add_library(SOURCES ${sources} PRIVATE_DEFINES INSIDE_DRIVER)
