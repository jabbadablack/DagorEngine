# OS API wrapper unit tests (named mounts)
set(sources main.cpp test_namedMounts.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  3rdPartyLibs/eastl
)

dagor_add_catch2_test(osApiWrappers-tests TAGS engine SOURCES ${sources} DEPS ${deps})
