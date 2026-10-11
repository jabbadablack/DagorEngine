# Ported from prog/gameLibs/render/deviceResetTelemetry/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude)
set(sources deviceResetTelemetry.cpp)
list(APPEND deps engine/lib3d gameLibs/statsd)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
