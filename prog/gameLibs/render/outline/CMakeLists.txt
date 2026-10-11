# Ported from prog/gameLibs/render/outline/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
)
set(SourceES outlineRendererCommonES.cpp.inl)
set(sources dasModules/outline.cpp)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} ES_SOURCES ${es_sources})
