# Data cache file backend unit tests
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources main.cpp test_fileBackend.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  gameLibs/datacache/file
)

dagor_add_catch2_test(datacacheFile-tests TAGS gameLibs SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
