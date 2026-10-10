# daNet unit tests
set(sources main.cpp bitStream.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  3rdPartyLibs/eastl
  engine/daNet
)

dagor_add_catch2_test(danet-tests TAGS engine net SOURCES ${sources} DEPS ${deps})
