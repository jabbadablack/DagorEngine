# Ported from prog/gameLibs/render/camouflage/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(SourceES camouflageOverrideParamsES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT QUIRREL PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
