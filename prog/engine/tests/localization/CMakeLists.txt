# Localization table unit tests
set(sources main.cpp test_duplicates.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/coreUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  3rdPartyLibs/eastl
)

dagor_add_catch2_test(localization-tests TAGS engine SOURCES ${sources} DEPS ${deps})
