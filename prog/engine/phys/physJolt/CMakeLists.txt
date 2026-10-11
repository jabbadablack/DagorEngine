# The engine's physics on Jolt (DAGOR_PHYS Jolt; the libraries link it through Dagor::Phys)
set(options)
dagor_deterministic_fp(options)

dagor_add_library(
  SOURCES
    joltPhysics.cpp
    joltPhysObject.cpp
    joltPhysRagdoll.cpp
    joltPhysSysInst.cpp
    joltDbgRender.cpp
    joltRayCar.cpp
    shapes/HeightField16Shape.cpp
    shapes/CollisionBlasShape.cpp
  PRIVATE_INCLUDES
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/3rdPartyLibs/phys/joltPhysics
    ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  PRIVATE_DEFINES USE_JOLT_PHYSICS VECMATH_NO_FMA # v_madd on NEON is explicit vfmaq that ignores ffp-contract=off
  COMPILE_OPTIONS ${options}
  DEPS
    engine/phys/physCommon
    3rdPartyLibs/phys/joltPhysics
    engine/heightMapLand
    engine/gameRes # CollResJoltChunk shares a CollisionResource::Data block
    Dagor::JoltSettings
)
