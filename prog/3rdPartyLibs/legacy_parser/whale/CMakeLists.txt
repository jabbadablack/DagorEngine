# whale, the LR parser generator of the shader compilers' parsers (with dolphin, see ../dolphin). jam built it rel only,
# into the source tree; here it is a program of the tree that the parser generation runs.
file(GLOB sources CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(options)
if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
  list(APPEND options -funsigned-char)
endif()
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND options -Wno-potentially-evaluated-expression)
  if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
    list(APPEND options -Wno-logical-op-parentheses -Wno-dangling-else)
  endif()
  if(DAGOR_PLATFORM STREQUAL "linux")
    list(APPEND options -Wno-deprecated-declarations -Wno-sometimes-uninitialized)
  endif()
endif()

dagor_add_executable(whale CONSOLE NO_CONFIG_POSTFIX
  EXCEPTIONS SEH
  RTTI ON
  SOURCES nstl/stl.cpp ${sources}
  PRIVATE_INCLUDES nstl hash
  PRIVATE_DEFINES NO_PCRE LR0_SUPPRESS_PROFILING __B_NO_MEM_BASE_INCLUDE
  COMPILE_OPTIONS ${options}
)
