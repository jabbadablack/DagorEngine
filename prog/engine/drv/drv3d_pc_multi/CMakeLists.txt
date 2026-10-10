# The 3d driver of the tree's programs (DAGOR_D3D_DRIVERS): the single driver itself, or, with several drivers (or
# DAGOR_D3D_MULTI_FORCED), the multi-driver interface that picks one at run time
set(drivers ${DAGOR_D3D_DRIVERS})
set(driver_deps ${drivers})
list(TRANSFORM driver_deps PREPEND "engine/drv/drv3d_")
if(NOT DAGOR_D3D_MULTI)
  dagor_add_library(INTERFACE DEPS ${driver_deps})
  return()
endif()

set(sources init.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  if("DX11" IN_LIST drivers OR "DX12" IN_LIST drivers)
    list(APPEND sources hlsl_dx.cpp)
  else()
    list(APPEND sources hlsl_stub.cpp)
  endif()
endif()
set(defines INSIDE_DRIVER)
foreach(driver IN LISTS drivers)
  list(APPEND defines USE_MULTI_D3D_${driver})
endforeach()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/engine/drv/drv3d_commonCode
    ${DAGOR_PROG_DIR}/3rdPartyLibs
  PRIVATE_DEFINES ${defines}
  DEPS engine/drv/drv3d_commonCode ${driver_deps}
)
