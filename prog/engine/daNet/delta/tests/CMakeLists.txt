# daNet delta compression unit tests
set(sources main.cpp netDelta.cpp)
list(APPEND deps
  engine/memory
  engine/kernel
  engine/osApiWrappers
  engine/baseUtil
  engine/ioSys
  engine/math
  engine/perfMon/daProfilerStub
  engine/daNet/delta
)

dagor_add_catch2_test(netdelta-tests TAGS engine net SOURCES ${sources} DEPS ${deps})
