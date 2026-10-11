# Ported from prog/gameLibs/decalMatrices/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources decalsMatrices.cpp)
list(APPEND deps engine/lib3d)
set(SourceES decalsMatrices.cpp)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
