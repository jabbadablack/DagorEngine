# Google's cpu_features: the CPU's vendor, model and instruction set extensions, per platform and architecture
set(sources src/filesystem.c src/stack_line_reader.c src/string_view.c src/impl_aarch64_cpuid.c)
set(c_options -DSTACK_LINE_READER_BUFFER_SIZE=1024)
set(source_options)
if(DAGOR_PLATFORM MATCHES "^(android|macOS)$")
  if(DAGOR_ARCH STREQUAL "arm64")
    # the hardware capabilities of an aarch64 unix (getauxval / sysctl)
    list(APPEND sources src/impl_aarch64_linux_or_android.c src/hwcaps_linux_or_android.c src/hwcaps_freebsd.c
      src/hwcaps.c)
    list(APPEND c_options -DHAVE_DLFCN_H)
    list(APPEND source_options src/hwcaps_linux_or_android.c -DHAVE_STRONG_GETAUXVAL)
  else()
    list(APPEND sources src/impl_x86_macos.c)
    list(APPEND c_options -DHAVE_SYSCTLBYNAME)
  endif()
elseif(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND sources src/impl_x86_linux_or_android.c src/impl_loongarch_linux.c src/impl_ppc_linux.c
    src/impl_riscv_linux.c src/impl_s390x_linux.c src/impl_aarch64_freebsd.c)
elseif(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources src/impl_x86_windows.c src/impl_aarch64_windows.c)
else()
  message(FATAL_ERROR "3rdPartyLibs/cpu_features does not support ${DAGOR_PLATFORM}")
endif()
if(DAGOR_PLATFORM MATCHES "^(iOS|macOS|tvOS)$" AND DAGOR_ARCH STREQUAL "arm64")
  list(APPEND sources src/impl_aarch64_macos_or_iphone.c)
  list(APPEND c_options -DHAVE_SYSCTLBYNAME)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES include include/internal
  C_OPTIONS ${c_options}
  SOURCE_OPTIONS ${source_options}
)
