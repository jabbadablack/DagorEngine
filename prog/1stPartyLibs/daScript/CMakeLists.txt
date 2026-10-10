# daScript: the compiler, runtime and builtin modules. Two builds, linked by the choice of each program:
#   1stPartyLibs.daScript.standard  log output through the engine
#   1stPartyLibs.daScript.console   stdout output and daScript's own crash handler, for the console tools (the das
#                                   interpreter) that set the DAGOR_DAS_CONSOLE target property
# Libraries depend on 1stPartyLibs/daScript, which links the one of the program they end up in.

set(source_dirs src/ast src/builtin src/runtime src/simulate src/misc src/parser src/modules/uriparser src/hal)
# project_specific_file_info.cpp provides fallbacks of get_file_access / get_context / get_clone_context that every
# Dagor program supplies itself (games through das_es.cpp + defaultFileAccess.cpp, tools through dagorAdapter/da.cpp),
# and src/hal/performance_time.cpp the time functions the engine kernel provides: they would be duplicate symbols
dagor_glob_sources(sources DIRS ${source_dirs} GLOB *.cpp EXCLUDE "project_specific_file_info\\.cpp$" "performance_time\\.cpp$")

# the sources that throw: compiled with exceptions whatever the tree's setting
set(exceptions)
if(DAGOR_MSVC_LIKE)
  set(exceptions /EHsc -D_HAS_EXCEPTIONS=1 -DDAS_ENABLE_EXCEPTIONS)
else()
  set(exceptions -fexceptions -DDAS_ENABLE_EXCEPTIONS)
endif()
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND exceptions -Wno-macro-redefined)
endif()
set(source_options)
foreach(source IN LISTS sources)
  if(source MATCHES "(_exceptions|_ast_serialize|runtime_string|format)\\.cpp$")
    list(APPEND source_options "${source}" ${exceptions})
  endif()
endforeach()
if(DAGOR_ARCH STREQUAL "e2k")
  list(APPEND source_options src/simulate/simulate_gc.cpp -Wno-overloaded-virtual)
endif()

set(defines DAS_ENABLE_KEEPALIVE=0 FMT_UNICODE=0 "$<$<CONFIG:Rel,IRel>:DAS_NO_ASSERTIONS=1>")
if(DAGOR_DAS_LLVM_AOT)
  list(APPEND defines DAS_LLVM_AOT)
endif()
set(options)
if(DAGOR_CC STREQUAL "gcc")
  list(APPEND options -Wno-stringop-overflow)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND options -Wno-deprecated-declarations)
endif()

foreach(build standard console)
  set(build_defines ${defines})
  if(build STREQUAL "console")
    list(APPEND build_defines DAS_DEFAULT_STDOUT DAS_USE_BASE_CRASH_HANDLER=1)
  endif()
  dagor_add_library(1stPartyLibs.daScript.${build}
    SOURCES ${sources}
    PRIVATE_INCLUDES
      include
      include/das_hash_map
      include/modules/uriparser
      ${DAGOR_PROG_DIR}/3rdPartyLibs/uriparser/include
      ${DAGOR_PROG_DIR}/3rdPartyLibs/fmt/include
    PRIVATE_DEFINES ${build_defines}
    COMPILE_OPTIONS ${options}
    SOURCE_OPTIONS ${source_options}
    DEPS 3rdPartyLibs/eastl 3rdPartyLibs/uriparser 3rdPartyLibs/fmt
    LICENSE_FILES LICENSE
    # the language's floats are IEEE: its comparisons and isnan/isinf see NaN and infinity (-ffinite-math-only would let
    # the compiler assume them away, and arm64 code then answers wrongly)
    PROPERTIES DAGOR_IEEE_MATH ON
  )
endforeach()
dagor_add_link_choice(1stPartyLibs.daScript PROPERTY DAGOR_DAS_CONSOLE
  ON 1stPartyLibs.daScript.console OFF 1stPartyLibs.daScript.standard)

# the daScript language and daslib test suite, run by the engine's das interpreter (dastest/tests is not included: it
# spawns '<exe> dastest.das' the way the standalone daslang host is invoked)
dagor_add_das_test(daScript.suite PATHS tests TAGS daScript TIMEOUT 1800)
