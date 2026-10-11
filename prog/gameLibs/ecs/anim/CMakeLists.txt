# Ported from prog/gameLibs/ecs/anim/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND deps 3rdPartyLibs/eastl gameLibs/render/animCharTexReplace)
set(SourceES
  animChar.cpp.inl
  slotAttachES.cpp.inl
  animStateES.cpp.inl
  animIrqES.cpp.inl
  randomAnimStarterES.cpp.inl
  animCharEffectorsES.cpp.inl
)
set(sources animUtils.cpp)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
