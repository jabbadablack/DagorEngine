# Fast physics: the simple point-mass and constraint simulation of character details (cloth, hair, chains). Programs
# with the DAGOR_MEASURE_PERF property get the build with profiling counters (MEASURE_PERF=1).
foreach(build standard measurePerf)
  set(defines)
  if(build STREQUAL "measurePerf")
    set(defines MEASURE_PERF=1)
  endif()
  dagor_add_library(engine.phys.fastPhys.${build}
    SOURCES fastPhys.cpp fastPhysDebug.cpp fastPhysRender.cpp
    PRIVATE_DEFINES ${defines}
  )
endforeach()
dagor_add_link_choice(engine.phys.fastPhys PROPERTY DAGOR_MEASURE_PERF
  ON engine.phys.fastPhys.measurePerf OFF engine.phys.fastPhys.standard)
