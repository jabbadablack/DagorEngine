# Ported from prog/gameLibs/ecs/game/generic/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources bindAnimSq.cpp)
list(APPEND deps 3rdPartyLibs/eastl)
set(SourceES )
dagor_glob_sources(SourceES DIRS . GLOB *ES.cpp.inl)
list(APPEND deps Dagor::Phys)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT
  QUIRREL
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
  ES_SOURCES ${es_sources}
)
