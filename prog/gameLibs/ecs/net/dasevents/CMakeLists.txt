# Ported from prog/gameLibs/ecs/net/dasevents/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include)
dagor_glob_sources(sources DIRS . GLOB *.cpp)
set(SourceES dasEventES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
