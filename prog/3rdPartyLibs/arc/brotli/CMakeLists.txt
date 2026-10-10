# Brotli compression
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/brotli/common
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/brotli/include
)
set(AllSrcFolder_C enc dec common)
dagor_glob_sources(sources DIRS ${AllSrcFolder_C} GLOB *.c)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
