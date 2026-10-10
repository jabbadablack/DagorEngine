# fmt {fmt} formatting (the engine's build replaces upstream's CMakeLists.txt)
set(includes include)
set(sources src/format.cc)
list(APPEND defines FMT_UNICODE=0)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND defines _HAS_EXCEPTIONS=1)
  list(APPEND options /EHsc)
else()
  list(APPEND options -fexceptions)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND options -Wno-macro-redefined)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
)
