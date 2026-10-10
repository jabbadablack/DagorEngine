# NodeBasedShader stubs for programs without node based shaders
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources nodeBasedShaderStub.cpp)
set(deps gameLibs/nodeBasedShaderManager/stub)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
