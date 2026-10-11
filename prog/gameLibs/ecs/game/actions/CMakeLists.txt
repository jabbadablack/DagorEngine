# Ported from prog/gameLibs/ecs/game/actions/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND es_sources actionES.cpp.inl)

dagor_add_library(STRICT PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
