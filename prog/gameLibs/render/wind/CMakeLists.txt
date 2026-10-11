# Ported from prog/gameLibs/render/wind/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources
  fluidWind.cpp
  ambientWind.cpp
  clusterWind.cpp
  clusterWindCascade.cpp
  clusterWindRenderer.cpp
  fxWindHelper.cpp
)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
