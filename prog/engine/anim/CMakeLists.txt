# Animation: blend trees, IK/FABRIK, post-blend controllers, the anim graph and its state. Programs with the
# DAGOR_MEASURE_PERF property get the build with profiling counters (MEASURE_PERF=1), as AssetViewer.
set(sources
  animBlendCtrl.cpp
  animPostBlendCtrl.cpp
  animIKCtrl.cpp
  animFABRIKCtrl.cpp
  animChannels.cpp
  animGraph.cpp
  animGraphDbg.cpp
  animStateHolder.cpp
  simpleNodeAnim.cpp
)
set(options)
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND options -Wno-undefined-bool-conversion)
endif()
foreach(build standard measurePerf)
  set(defines)
  if(build STREQUAL "measurePerf")
    set(defines MEASURE_PERF=1)
  endif()
  dagor_add_library(engine.anim.${build} STRICT
    SOURCES ${sources}
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/acl/includes
    PRIVATE_DEFINES ${defines}
    COMPILE_OPTIONS ${options}
    DEPS 3rdPartyLibs/regExp
  )
endforeach()
dagor_add_link_choice(engine.anim PROPERTY DAGOR_MEASURE_PERF ON engine.anim.measurePerf OFF engine.anim.standard)
