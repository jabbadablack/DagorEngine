# Ported from prog/gameLibs/ecs/console/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/engine/consoleProc
)
set(sources ecsConsole.cpp)
list(APPEND deps 3rdPartyLibs/eastl)
set(SourceES )
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
