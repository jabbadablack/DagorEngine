# Ported from prog/engine/daECS/scene/jamfile (jam2cmake/skeleton.py)
set(sources scene.cpp)
list(APPEND deps engine/daECS/io/datablock engine/daECS/core 3rdPartyLibs/eastl)

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
