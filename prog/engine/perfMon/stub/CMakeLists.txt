# Performance monitoring stubs (misc counters, cache simulation) for programs without the profiler
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/engine/perfMon)
set(sources misc.cpp cachesim.cpp)
set(deps engine/perfMon/daProfilerStub engine/perfMon/gpuProfilerStub engine/perfMon/perfTimerStub)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
