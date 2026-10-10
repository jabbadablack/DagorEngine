# libpng 1.4.22 (on zlib-ng)
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng)
set(sources
  png.c
  pngerror.c
  pngget.c
  pngmem.c
  pngpread.c
  pngread.c
  pngrio.c
  pngrtran.c
  pngrutil.c
  pngset.c
  pngtrans.c
  pngwio.c
  pngwrite.c
  pngwtran.c
  pngwutil.c
)
set(defines PNG_NO_CONSOLE_IO PNG_NO_WRITE_FLUSH)
if(DAGOR_ARCH STREQUAL "x86_64" AND DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND c_options /wd4267)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} C_OPTIONS ${c_options})
