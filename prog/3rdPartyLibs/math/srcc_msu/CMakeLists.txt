# is01r spline smoothing, a numerical routine translated from Fortran with f2c (origin unknown, see NO_LICENSE)
set(sources is01r_c.c)
list(APPEND force_includes supp/dag_null.h)

dagor_add_library(SOURCES ${sources} FORCE_INCLUDES ${force_includes})
