# HTTP streaming unit tests (against a local HTTP server)
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources main.cpp test_streamIO.cpp)
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
  gameLibs/streamIO
)

dagor_add_catch2_test(streamIO-tests TAGS gameLibs net
  REQUIRES http_server
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  DEPS ${deps}
)
