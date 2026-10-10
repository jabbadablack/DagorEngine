# daECS game resource stubs for programs without game resources
set(sources gameResStub.cpp)
list(APPEND deps engine/daECS/core 3rdPartyLibs/eastl)

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
