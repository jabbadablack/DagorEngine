# SMOL-V: a smaller, more compressible encoding of SPIR-V shader programs
set(includes source)
set(sources source/smolv.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(defines WIN32 NDEBUG _CONSOLE GENERIC_COMPILER YYDEBUG=0)
  set(options /d2Zi+)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
)
