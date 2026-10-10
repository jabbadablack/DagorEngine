# System information (OS, CPU, GPU and memory) for logs and crash reports; a stub where a platform has none
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND includes ${DAGOR_ENGINE_ROOT}/3rdPartyLibs/eastl/include)
  set(sources win/systemId.cpp)
  list(APPEND libs advapi32)
else()
  set(sources stub/sysinfo.cpp)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} SYSTEM_LIBS ${libs})
