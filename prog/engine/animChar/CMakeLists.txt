# Animated characters: the anim char (skeleton, anim graph state, physics), its rendering and the second animation
# pass. Programs with the DAGOR_MEASURE_PERF property get the build with profiling counters (MEASURE_PERF=1).
set(options)
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND options -Wno-undefined-bool-conversion)
endif()
foreach(build standard measurePerf)
  set(defines)
  if(build STREQUAL "measurePerf")
    set(defines MEASURE_PERF=1)
  endif()
  dagor_add_library(engine.animChar.${build} STRICT
    SOURCES animCharacter2.cpp animCharBase.cpp animCharRend.cpp animate2ndPass.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/acl/includes
    PRIVATE_DEFINES ${defines}
    COMPILE_OPTIONS ${options}
    DEPS engine/anim engine/phys/fastPhys
  )
endforeach()
dagor_add_link_choice(engine.animChar PROPERTY DAGOR_MEASURE_PERF
  ON engine.animChar.measurePerf OFF engine.animChar.standard)
