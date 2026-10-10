# Game resources: the resource packs (grp), their descriptions and loading, the factories of the resource types
set(sources
  gameResSystem.cpp
  gameResPackList.cpp
  gameResHooks.cpp
  gameResDescBin.cpp
  gameResOptionalPacks.cpp
  a2d_gameres.cpp
  animCharGameRes.cpp
  characterGameRes.cpp
  dynModelGameRes.cpp
  effectGameRes.cpp
  fastPhysGameRes.cpp
  geomNodeTreeGameRes.cpp
  physObjGameRes.cpp
  physSysGameRes.cpp
  rendInstGameRes.cpp
  materialGameRes.cpp
  lshaderGameRes.cpp
  impostorDataGameRes.cpp
  collisionDebug.cpp
  collisionFactory.cpp
  collisionGameRes.cpp
  collisionGameResLoad.cpp
  collisionResourceBuilder.cpp
  collisionResourceInstance.cpp
  collisionTraceOOL.cpp
  stubGameResFactories.cpp
)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
list(APPEND deps 3rdPartyLibs/eastl engine/daBVH)
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND options -Wno-undefined-bool-conversion)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$" AND DAGOR_ARCH STREQUAL "e2k")
  list(APPEND source_options collisionGameRes.cpp -Wno-pass-failed)
endif()
if(DAGOR_LTO AND DAGOR_CC STREQUAL "msvc" AND DAGOR_ARCH STREQUAL "arm64")
  list(APPEND source_options collisionGameRes.cpp /GL-) # MSVC's arm64 LTO miscompiles it
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  COMPILE_OPTIONS ${options}
  SOURCE_OPTIONS ${source_options}
  DEPS ${deps}
)
