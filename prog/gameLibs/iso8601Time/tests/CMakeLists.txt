# ISO 8601 time unit tests
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources main.cpp test_iso8601.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  gameLibs/iso8601Time
)

dagor_add_catch2_test(iso8601Time-tests TAGS gameLibs SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
