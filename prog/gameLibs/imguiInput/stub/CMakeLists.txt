# Ported from prog/gameLibs/imguiInput/stub/jamfile (jam2cmake/skeleton.py)
set(sources imguiInput_stub.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(deps engine/imgui/stub)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
