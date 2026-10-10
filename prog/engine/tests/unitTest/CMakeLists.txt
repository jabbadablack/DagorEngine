# Unit tests of the unit test harness itself (image compare, test environment, failures)
set(sources main.cpp test_imageCompare.cpp test_testEnv.cpp test_harnessFailures.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/image
  engine/perfMon/daProfilerStub
  3rdPartyLibs/eastl
)

dagor_add_catch2_test(unitTest-tests TAGS engine SOURCES ${sources} DEPS ${deps})
