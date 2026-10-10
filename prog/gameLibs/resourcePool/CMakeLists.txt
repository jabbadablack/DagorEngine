# Pools of reusable GPU resources and aliasable managed 2D textures
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources aliasableTex.cpp resourcePool.cpp)
list(APPEND deps engine/lib3d)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
