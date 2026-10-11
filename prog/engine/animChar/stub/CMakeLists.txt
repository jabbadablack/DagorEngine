# Ported from prog/engine/animChar/stub/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/dagorInclude)
set(sources animCharStub.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
