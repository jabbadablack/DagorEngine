# Ported from prog/gameLibs/ecs/gameres/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources commonLoadingJobMgr.cpp)
list(APPEND es_sources gameResES.cpp.inl)
list(APPEND deps 3rdPartyLibs/eastl)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
