# Ported from prog/gameLibs/statsd/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources statsd.cpp log.cpp)
list(APPEND deps gameLibs/asyncResolveAddr)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
