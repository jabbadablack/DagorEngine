# MinHook API hooking (the kernel's hardware breakpoints on Windows)
set(sources src/hde/hde32.c src/hde/hde64.c src/buffer.c src/hook.c src/trampoline.c)

dagor_add_library(SOURCES ${sources})
