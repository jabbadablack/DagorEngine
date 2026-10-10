# Quirrel: the VM and its standard library (the engine's build replaces upstream's CMakeLists.txt; the compiler is
# squirrel/compiler, the module system sqmodules)
set(sources
  squirrel/sqapi.cpp
  squirrel/sqbaselib.cpp
  squirrel/sqclass.cpp
  squirrel/sqdebug.cpp
  squirrel/sqobject.cpp
  squirrel/sqstate.cpp
  squirrel/sqtable.cpp
  squirrel/sqvm.cpp
  squirrel/sqdedupshrinker.cpp
  squirrel/sqstringlib.cpp
  squirrel/sqext.cpp
  squirrel/sqasync.cpp
  squirrel/sqmem.cpp
  sqstdlib/sqstdrex.cpp
  sqstdlib/sqstdaux.cpp
  sqstdlib/sqstdmath.cpp
  sqstdlib/sqstdstring.cpp
  sqstdlib/sqstdblob.cpp
  sqstdlib/sqstddebug.cpp
  sqstdlib/sqstdhash.cpp
  sqstdlib/sqstdio.cpp
  sqstdlib/sqstdstream.cpp
  sqstdlib/sqstdsystem.cpp
  sqstdlib/sqstddatetime.cpp
  sqstdlib/sqstdserialization.cpp
)
set(defines SQ_EXCLUDE_DEFAULT_MEMFUNCTIONS
  "$<IF:$<CONFIG:Rel,IRel>,SQ_RUNTIME_TYPE_CHECK=0;SQ_STACK_DUMP_SECRET_PREFIX=no_dump_,SQ_CHECK_THREAD;SQ_RANDOMIZE_FOREACH=1>")
if(DAGOR_SQ_VAR_TRACE)
  list(APPEND sources squirrel/vartrace.cpp)
  list(APPEND defines SQ_VAR_TRACE_ENABLED)
else()
  list(APPEND sources squirrel/vartracestub.cpp)
endif()
if(NOT DAGOR_PLATFORM MATCHES "^(windows|linux|macOS)$")
  list(APPEND defines SQ_SYSTEM_STUBS=1)
endif()

dagor_add_library(QUIRREL_HEADERS
  SOURCES ${sources}
  PRIVATE_INCLUDES squirrel internal helpers
  PRIVATE_DEFINES ${defines}
  DEPS 3rdPartyLibs/eastl 1stPartyLibs/quirrel/quirrel/squirrel/compiler
  LICENSE_FILES COPYRIGHT
)
