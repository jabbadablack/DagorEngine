# Ported from prog/engine/daECS/hierarchyTransform/jamfile (jam2cmake/skeleton.py)
list(APPEND deps 3rdPartyLibs/eastl)
set(SourceES hierarchyTransformES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT DEPS ${deps} ES_SOURCES ${es_sources})
