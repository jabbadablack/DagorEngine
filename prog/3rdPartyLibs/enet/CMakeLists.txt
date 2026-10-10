# ENet reliable UDP networking
set(sources callbacks.c compress.c enet_dagor.c host.c list.c packet.c peer.c protocol.c)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources win32.c)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|iOS|linux|macOS|tvOS)$")
  list(APPEND sources unix.c)
endif()
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/enet/include)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND libs winmm ws2_32)
elseif(DAGOR_PLATFORM MATCHES "^(android|iOS|linux|macOS|tvOS)$")
  list(APPEND defines HAS_SOCKLEN_T HAS_POLL HAS_INET_NTOP HAS_INET_PTON HAS_MSGHDR_FLAGS SOMAXCONN=128)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl|gcc)$")
  list(APPEND options -Wno-unused-parameter)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  SYSTEM_LIBS ${libs}
)
