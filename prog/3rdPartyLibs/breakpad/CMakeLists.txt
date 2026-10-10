# Google Breakpad's crash handling client: minidump writing and the exception handler
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/breakpad
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/engine/kernel
)
set(deps 3rdPartyLibs/arc/zlib-ng)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND defines UNICODE)
  list(APPEND deps 3rdPartyLibs/breakpad/common/windows)
  set(sources
    client/windows/crash_generation/minidump_generator.cc
    client/windows/crash_generation/client_info.cc
    client/windows/crash_generation/crash_generation_client.cc
    client/windows/handler/exception_handler.cc
  )
endif()
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps 3rdPartyLibs/breakpad/common 3rdPartyLibs/breakpad/common/linux)
  set(sources
    client/linux/crash_generation/crash_generation_client.cc
    client/linux/minidump_writer/linux_dumper.cc
    client/linux/minidump_writer/linux_ptrace_dumper.cc
    client/linux/minidump_writer/linux_core_dumper.cc
    client/linux/minidump_writer/minidump_writer.cc
    client/linux/microdump_writer/microdump_writer.cc
    client/linux/handler/exception_handler.cc
    client/linux/handler/minidump_descriptor.cc
    client/linux/dump_writer_common/thread_info.cc
    client/linux/dump_writer_common/ucontext_reader.cc
    client/linux/dump_writer_common/seccomp_unwinder.cc
    client/linux/log/log.cc
    client/minidump_file_writer.cc
  )
endif()
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND deps 3rdPartyLibs/breakpad/common 3rdPartyLibs/breakpad/common/mac)
  set(sources
    client/mac/handler/breakpad_nlist_64.cc
    client/mac/handler/dynamic_images.cc
    client/mac/handler/exception_handler.cc
    client/mac/handler/minidump_generator.cc
    client/mac/handler/protected_memory_allocator.cc
    client/minidump_file_writer.cc
  )
  list(APPEND libs pthread)
endif()
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND options -Wno-stack-protector)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  SYSTEM_LIBS ${libs}
)
