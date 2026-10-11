# Ported from prog/gameLibs/ecs/render/weather_effects/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND deps 3rdPartyLibs/eastl)
set(SourceES lightningES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
