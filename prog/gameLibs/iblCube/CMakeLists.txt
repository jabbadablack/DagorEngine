# Ported from prog/gameLibs/iblCube/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(SourceES render/iblCubeES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
