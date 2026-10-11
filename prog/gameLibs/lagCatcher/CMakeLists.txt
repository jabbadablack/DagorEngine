# Ported from prog/gameLibs/lagCatcher/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources lagCatcher.cpp)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND sources btCollector.cpp utils.cpp)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
