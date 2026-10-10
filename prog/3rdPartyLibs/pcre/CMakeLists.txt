# PCRE 8.31 (classic PCRE1) with the JIT compiler and the C++ wrapper; per-platform generated character tables
if(DAGOR_PLATFORM STREQUAL "windows")
  set(includes win32)
  set(sources win32/pcre_chartables.c)
elseif(DAGOR_PLATFORM STREQUAL "android")
  set(includes linux32)
  set(sources linux32/pcre_chartables.c)
elseif(DAGOR_PLATFORM STREQUAL "linux")
  set(includes linux64)
  set(sources linux64/pcre_chartables.c)
elseif(DAGOR_PLATFORM MATCHES "^(iOS|macOS|tvOS)$")
  set(includes macosx)
  set(sources macosx/pcre_chartables.c)
endif()
list(APPEND includes pcre)
list(APPEND sources
  pcre/pcre_byte_order.c
  pcre/pcre_compile.c
  pcre/pcre_config.c
  pcre/pcre_dfa_exec.c
  pcre/pcre_exec.c
  pcre/pcre_fullinfo.c
  pcre/pcre_get.c
  pcre/pcre_globals.c
  pcre/pcre_jit_compile.c
  pcre/pcre_maketables.c
  pcre/pcre_newline.c
  pcre/pcre_ord2utf8.c
  pcre/pcre_printint.c
  pcre/pcre_refcount.c
  pcre/pcre_string_utils.c
  pcre/pcre_study.c
  pcre/pcre_tables.c
  pcre/pcre_ucd.c
  pcre/pcre_valid_utf8.c
  pcre/pcre_version.c
  pcre/pcre_xclass.c
  pcre/pcrecpp.cc
  pcre/pcre_scanner.cc
  pcre/pcre_stringpiece.cc
  pcre/pcrecpp_nostl.cc
)
set(defines HAVE_CONFIG_H)
set(c_options -DHAVE_CONFIG_H)
if(DAGOR_CC MATCHES "^(clang|clang\-cl|gcc)$")
  list(APPEND options -Wno-unused-parameter)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  C_OPTIONS ${c_options}
)
