# The game's collision (prog/gameLibs/gamePhys/collision/jamfile-General, built without APEX): the sources are in the
# parent dir
set(options)
dagor_deterministic_fp(options)

dagor_add_library(STRICT
  SOURCES
    ../collisionResponse.cpp
    ../collisionLib.cpp
    ../collisionInstances.cpp
    ../rendinstCollision.cpp
    ../traceLib.cpp
    ../collisionLinks.cpp
    ../contactSolver.cpp
    ../collisionCache.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/engine/sharedInclude # gameRes/collisionResourceBuilder.h
  PRIVATE_DEFINES VECMATH_NO_FMA # v_madd on NEON is explicit vfmaq that ignores ffp-contract=off
  COMPILE_OPTIONS ${options}
  DEPS Dagor::Phys engine/sceneRay gameLibs/rendInst gameLibs/physMap gameLibs/fftWater
)
