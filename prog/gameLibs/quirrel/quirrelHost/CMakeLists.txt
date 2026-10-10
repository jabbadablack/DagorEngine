# The Quirrel host of the engine: memory allocation through the engine and memory tracing
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/quirrel/quirrel/squirrel
  ${DAGOR_PROG_DIR}/1stPartyLibs/quirrel/quirrel/internal
)
set(sources memtrace.cpp sqmem_dagor.cpp)
# no reuse of freed blocks under the sanitizers other than ASan (as jam built it: its condition held for no sanitizer)
if(NOT DAGOR_SANITIZE MATCHES "^(none|address)$")
  list(APPEND source_options sqmem_dagor.cpp -DENABLE_RE_USE=0)
endif()
if(DAGOR_SQ_VAR_TRACE)
  list(APPEND defines SQ_VAR_TRACE_ENABLED)
endif()

dagor_add_library(QUIRREL_HEADERS
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  SOURCE_OPTIONS ${source_options}
)
