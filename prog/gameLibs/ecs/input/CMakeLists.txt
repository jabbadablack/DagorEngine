# Ported from prog/gameLibs/ecs/input/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources esHidEventRouter.cpp input.cpp debugInputEvents.cpp)
set(SourceES rumbleES.cpp.inl)
list(APPEND es_sources ${SourceES})
list(APPEND deps gameLibs/daInput)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
