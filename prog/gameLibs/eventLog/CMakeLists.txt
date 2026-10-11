# Ported from prog/gameLibs/eventLog/jamfile (jam2cmake/skeleton.py)
set(sources dataHelpers.cpp eventLog.cpp errorLog.cpp httpRequest.cpp)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/sysinfo
)
list(APPEND deps 1stPartyLibs/jsoncpp 1stPartyLibs/sysinfo gameLibs/asyncHTTPClient gameLibs/asyncResolveAddr)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
