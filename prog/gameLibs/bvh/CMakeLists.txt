# BVH ray tracing (DAGOR_GAME_BVH), or its stub. The parts of the scene it covers are features, each with its stub;
# DAGOR_BVH_STUBS lists those a tree builds as stubs (a game's: DagorGame.cmake).
if(NOT DAGOR_GAME_BVH)
  dagor_add_library(STRICT
    SOURCES stub/bvh_stub.cpp stub/bvh_stub_processors.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
    DEPS gameLibs/userSystemInfo gameLibs/eventLog
  )
  return()
endif()

set(sources bvh.cpp bvh_context.cpp bvh_debug.cpp bvh_tlas_debug.cpp bvh_omm.cpp bvh_processors.cpp bvh_particles.cpp
  bvh_voxel_activity.cpp)
set(deps gameLibs/userSystemInfo gameLibs/eventLog gameLibs/render/omm)
# <feature> is bvh_<feature>.cpp, or stub/bvh_stub_<feature>.cpp; ri has more
set(features terrain ri dyn gobj grass cables bin_scene fft_water dagdp gpu_grass splinegen fx lru_collision
  smoke_tracers)
foreach(stub IN LISTS DAGOR_BVH_STUBS)
  if(NOT stub IN_LIST features)
    message(FATAL_ERROR "DAGOR_BVH_STUBS: no BVH feature '${stub}' (the features: ${features})")
  endif()
endforeach()
foreach(feature IN LISTS features)
  if(feature IN_LIST DAGOR_BVH_STUBS)
    list(APPEND sources stub/bvh_stub_${feature}.cpp)
  elseif(feature STREQUAL "ri")
    list(APPEND sources bvh_ri.cpp bvh_ri_gen.cpp bvh_ri_ex.cpp)
  else()
    list(APPEND sources bvh_${feature}.cpp)
    if(feature STREQUAL "lru_collision")
      list(APPEND deps gameLibs/render/lruCollision)
    endif()
  endif()
endforeach()
set(options)
if(DAGOR_CC STREQUAL "msvc")
  list(APPEND options /wd4582 /wd5031)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
