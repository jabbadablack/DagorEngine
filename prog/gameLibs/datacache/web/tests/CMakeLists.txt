# Data cache web backend unit tests (against a local HTTP server)
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng)
set(sources main.cpp test_webBackend.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/coreUtil
  engine/startup
  engine/perfMon/daProfilerStub
  gameLibs/datacache/web
  3rdPartyLibs/arc/zlib-ng
)
list(APPEND defines OPENSSL_SUPPRESS_DEPRECATED)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)

dagor_add_catch2_test(datacacheWeb-tests TAGS gameLibs net
  REQUIRES http_server
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  DEPS ${deps}
)
