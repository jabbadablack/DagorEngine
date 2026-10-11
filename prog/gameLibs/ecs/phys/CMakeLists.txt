# Ported from prog/gameLibs/ecs/phys/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
set(sources netPhysResync.cpp collRes.cpp collResFromEcs.cpp collResFromRI.cpp)
list(APPEND deps 3rdPartyLibs/eastl)
set(SourceES
  animCharFastPhysDebug.cpp.inl
  particlePhysSys.cpp
  animPhysES.cpp.inl
  animCharFastPhysES.cpp.inl
  physBodyES.cpp.inl
  ragdollES.cpp.inl
  physVarsES.cpp.inl
  gravityES.cpp.inl
  segHumanPhysES.cpp.inl
  turretControlES.cpp.inl
)
list(APPEND deps Dagor::Phys)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
