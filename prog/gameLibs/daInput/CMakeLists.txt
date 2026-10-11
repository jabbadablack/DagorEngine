# Ported from prog/gameLibs/daInput/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/3rdPartyLibs/pcre/pcre
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
)
set(sources
  actionData.cpp
  actionsAndBindings.cpp
  actionProcessing.cpp
  userConfig.cpp
  actionSqBind.cpp
  dargSqBind.cpp
  actionsDbg.cpp
)
list(APPEND deps 3rdPartyLibs/eastl)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
