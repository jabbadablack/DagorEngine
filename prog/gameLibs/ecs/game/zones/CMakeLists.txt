# Ported from prog/gameLibs/ecs/game/zones/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(SourceES )
dagor_glob_sources(SourceES DIRS . GLOB *ES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT QUIRREL PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
