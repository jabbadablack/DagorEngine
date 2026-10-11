# Ported from prog/gameLibs/imguiInput/jamfile (jam2cmake/skeleton.py)
set(sources imguiInput.cpp imguiInputHandler.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(deps 3rdPartyLibs/eastl 3rdPartyLibs/imgui engine/imgui gameLibs/daInput)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
