# dolphin, the lexer generator of the shader compilers' parsers (with whale, see ../whale). jam built it rel only, into
# the source tree; here it is a program of the tree that the parser generation runs, and part of the CDK.
file(GLOB sources CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(options)
if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
  list(APPEND options -funsigned-char)
endif()
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND options -Wno-potentially-evaluated-expression)
  if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
    list(APPEND options -Wno-deprecated-declarations)
  endif()
  if(DAGOR_PLATFORM STREQUAL "linux")
    list(APPEND options -Wno-sometimes-uninitialized)
  endif()
endif()

dagor_add_executable(dolphin CONSOLE CDK NO_CONFIG_POSTFIX
  EXCEPTIONS SEH
  RTTI ON
  SOURCES ${sources}
  PRIVATE_INCLUDES nstl hash
  PRIVATE_DEFINES __B_NO_MEM_BASE_INCLUDE
  COMPILE_OPTIONS ${options}
)
