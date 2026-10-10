# Base utilities: strings, hashing, fast name maps, time, threads helpers
set(sources
  fastStrMap.cpp
  oaHashNameMap.cpp
  tabMem.cpp
  tabSorted.cpp
  strImpl.cpp
  dobject.cpp
  fatalCtx.cpp
  bitArray.cpp
  syncExecScheduler.cpp
  hierBitMem.cpp
  restart.cpp
  texMetaData.cpp
  unicodeHlp.cpp
  safeArg.cpp
  threadPool.cpp
  parallelFor.cpp
  watchdog.cpp
  delayedActions.cpp
  treeBitmap.cpp
  lag.cpp
  fnameMap.cpp
  fileMd5Validate.cpp
)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(defines __B_KERNEL_LIB)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines})
