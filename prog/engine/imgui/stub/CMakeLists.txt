# ImGui integration stubs: the engine's imgui_* API with ImGui always off
set(sources imguiImpl_stub.cpp)
set(deps 3rdPartyLibs/imgui)

dagor_add_library(SOURCES ${sources} DEPS ${deps})
