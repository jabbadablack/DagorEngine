# POSIX functions missing on Windows (inet_ntop, inet_pton)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(sources src/inet_ntop.c src/inet_pton.c)
endif()
list(APPEND force_includes supp/dag_null.h)

dagor_add_library(STRICT SOURCES ${sources} FORCE_INCLUDES ${force_includes})
