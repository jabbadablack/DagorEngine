# binBlk: converts BLK files between text and binary form (the CDK's; jam built it rel only, so without a config
# suffix). The other utilities of this directory (jamfile, jamfile-misc) are not ported yet.
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/baseUtil
  engine/perfMon/daProfilerStub
  tools/libTools/util
  3rdPartyLibs/openssl-3.x
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(binBlk CONSOLE CDK NO_CONFIG_POSTFIX
  SOURCES binblk.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include
  DEPS ${deps}
)
