# daProfiler: the engine's CPU/GPU profiler with its capture and dump formats
set(includes ${DAGOR_PROG_DIR}/engine/perfMon/daProfiler ${DAGOR_PROG_DIR}/engine/sharedInclude)
if(DAGOR_PLATFORM STREQUAL "android")
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/libunwind/include)
  list(APPEND deps 3rdPartyLibs/libunwind)
endif()
set(sources
  daProfiler.cpp
  daProfilerPlugins.cpp
  daProfilePageAllocator.cpp
  daProfilerOOL.cpp
  daProfilerThreads.cpp
  daProfilerVSDump.cpp
  daProfilerMessageServer.cpp
  daProfilerDefaultMessages.cpp
  daProfilerDumpServer.cpp
  daProfilerDescriptions.cpp
  daProfilerDataDescriptions.cpp
  daProfilerSampling.cpp
  daProfilerDumpHier.cpp
  daProfilerSaveDump.cpp
  daProfilerPrepareDump.cpp
  daProfilerPlatform.cpp
  daProfilerPlatformGPU.cpp
  daProfilerFileDump.cpp
  daProfilerLogDump.cpp
  daProfilerNetServer.cpp
  daProfilerUserSettings.cpp
  daProfilerUserSettingsDump.cpp
  daProfilerSymbolsCache.cpp
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources stackUnwinder/unwindStackWin.cpp)
elseif(DAGOR_PLATFORM STREQUAL "android")
  list(APPEND sources stackUnwinder/unwindStackAndroid.cpp)
elseif(DAGOR_PLATFORM MATCHES "^(iOS|macOS|tvOS)$")
  list(APPEND sources stackUnwinder/unwindStackMac.cpp)
else()
  list(APPEND sources stackUnwinder/unwindStackDagor.cpp)
endif()
set(defines __B_KERNEL_LIB)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
