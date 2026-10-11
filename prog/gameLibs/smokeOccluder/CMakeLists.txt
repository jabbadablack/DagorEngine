# Ported from prog/gameLibs/smokeOccluder/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(SourceES smokeOccluderES.cpp.inl)
list(APPEND es_sources ${SourceES})
list(APPEND deps engine/daECS/core)

dagor_add_library(STRICT PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
