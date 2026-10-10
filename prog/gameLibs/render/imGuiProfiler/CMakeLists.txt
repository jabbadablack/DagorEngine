# The ImGui profiler window: CPU and GPU timings of the profiler's events, with draw stats
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources imGuiProfiler.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
