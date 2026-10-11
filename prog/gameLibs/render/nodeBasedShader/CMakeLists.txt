# Ported from prog/gameLibs/render/nodeBasedShader/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources nodeBasedShader.cpp)
set(SourceES nodeBasedShaderES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
