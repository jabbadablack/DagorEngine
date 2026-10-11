# Ported from prog/gameLibs/userSystemInfo/jamfile (jam2cmake/skeleton.py; no Steam or Epic store libraries in the fork)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/compressionUtils
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/tools/sharedInclude
)
set(sources systemInfo.cpp dumpSysInfo.cpp userSystemInfo.cpp uuidgen.cpp redistInfo.cpp)
list(APPEND sources systemInfo_stubext.cpp) # the fork has no systemInfo_private.cpp
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
list(APPEND deps 3rdPartyLibs/openssl-3.x)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs iphlpapi rpcrt4 wbemuuid)
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources macosx_spec.mm)
  list(APPEND libs -Wl,-framework,DiskArbitration -Wl,-framework,IOKit)
endif()
if(DAGOR_PLATFORM STREQUAL "iOS")
  list(APPEND deps gameLibs/ios/net_reachability)
  list(APPEND sources ios_spec.mm)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|linux|macOS|windows)$" AND NOT DAGOR_ARCH STREQUAL "e2k")
  list(APPEND deps 3rdPartyLibs/cpu_features)
  list(APPEND defines USE_CPU_FEATURES)
endif()
list(APPEND deps 3rdPartyLibs/hash engine/drv/vr_device)
if(DAGOR_PLATFORM MATCHES "^(android|iOS|linux|macOS|windows)$")
  list(APPEND deps gameLibs/folders)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
