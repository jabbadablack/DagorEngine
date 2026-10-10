# Fatal errors, logging, debug dumps, CPU frequency and hardware exception handling
set(sources
  fatalerr.cpp
  kernelGlobalSetting.cpp
  globalVars/occlusion_map.cpp
  globalVars/hdrMode.cpp
  cdebug.c
  debugDumpStack.cpp
  logimpl.cpp
  writeStream.cpp
  cpuControl.cpp
  perfTimer.cpp
)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources cpuFreq.cpp dagorHwExcept.cpp debug.cpp dagorMinidumpCallback.cpp)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources debug.cpp macosx/macCpuFreq.cpp macosx/macGlobVars.cpp dagorHwExcept.cpp)
elseif(DAGOR_PLATFORM STREQUAL "iOS")
  list(APPEND sources macosx/macCpuFreq.cpp macosx/macGlobVars.cpp dagorHwExcept.cpp mobile_debug.cpp)
elseif(DAGOR_PLATFORM STREQUAL "tvOS")
  list(APPEND sources macosx/macCpuFreq.cpp dagorHwExcept.cpp)
elseif(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND sources debug.cpp linux/linuxCpuFreq.cpp dagorHwExcept.cpp)
elseif(DAGOR_PLATFORM STREQUAL "android")
  # TODO(android): android/android.bundle/src/DagorLogger.java and and.proguard go into the APK
  list(APPEND sources linux/linuxCpuFreq.cpp dagorHwExcept.cpp mobile_debug.cpp and_native_app.c
    and_native_activity.cpp android/jni_native_reg.cpp)
endif()

# the hardware breakpoints (Windows x64, through minhook) are not in Rel; with DAGOR_FORCE_LOGS Rel encrypts its logs
set(dir "${CMAKE_CURRENT_SOURCE_DIR}")
set(not_rel "$<NOT:$<CONFIG:Rel>>")
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(deps)
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64")
  list(APPEND sources "$<${not_rel}:${dir}/dagorHwBreakpoint.cpp>")
  list(APPEND includes "$<${not_rel}:${DAGOR_PROG_DIR}/3rdPartyLibs/minhook/Include>")
  dagor_use(3rdPartyLibs/minhook)
  list(APPEND deps "$<${not_rel}:3rdPartyLibs.minhook>")
else()
  list(APPEND sources "$<${not_rel}:${dir}/stub/dagorHwBreakpoint.cpp>")
endif()
if(DAGOR_FORCE_LOGS)
  list(APPEND sources "$<$<CONFIG:Rel>:${dir}/def_logCryptKey.cpp>")
endif()

set(defines __B_KERNEL_LIB __B_NO_MEM_BASE_INCLUDE)
if(NOT DAGOR_SANITIZE STREQUAL "none" AND DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
  list(APPEND defines DAGOR_CAPTURE_STDERR) # the sanitizers write to stderr; this disables asynchronous log writes
endif()
if(DAGOR_PLATFORM STREQUAL "android")
  list(APPEND includes ${DAGOR_ANDROID_NDK}/sources/android/cpufeatures)
endif()
if(DAGOR_BREAKPAD)
  list(APPEND defines __BREAKPAD_ENABLED)
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/breakpad)
  list(APPEND deps 3rdPartyLibs/breakpad)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
