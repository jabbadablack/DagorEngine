# Ported from prog/3rdPartyLibs/bsdiff/jamfile (jam2cmake/skeleton.py)
set(sources bsdiff.c bspatch.c)
list(APPEND force_includes supp/dag_null.h)

dagor_add_library(SOURCES ${sources} FORCE_INCLUDES ${force_includes})
