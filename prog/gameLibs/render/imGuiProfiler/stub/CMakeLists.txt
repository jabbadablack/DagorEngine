# ImGui profiler window stub for programs without it
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources imGuiProfilerStub.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
