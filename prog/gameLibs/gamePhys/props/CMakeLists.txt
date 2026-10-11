# Ported from prog/gameLibs/gamePhys/props/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources
  atmosphere.cpp
  shakeMatProps.cpp
  deformMatProps.cpp
  arcadeBoostProps.cpp
  softMaterialProps.cpp
  physMatDamageModelProps.cpp
  physDestructibleProps.cpp
  physContactProps.cpp
)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
