# The work cycle stub for programs without the engine's main loop (console tools on Linux). Flavor perf: with the
# perf-timing stubs as well (WORKCYCLE_PERF_STUB), e.g. engine/workCycle/stub:perf for benchmarks.
function(_workCycleStub flavor)
  set(defines)
  if(flavor STREQUAL "perf")
    set(defines WORKCYCLE_PERF_STUB)
  elseif(flavor)
    message(FATAL_ERROR "engine/workCycle/stub has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} STRICT
    SOURCES wcstub.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/workCycle
    PRIVATE_DEFINES ${defines}
  )
endfunction()

dagor_flavors(_workCycleStub)
