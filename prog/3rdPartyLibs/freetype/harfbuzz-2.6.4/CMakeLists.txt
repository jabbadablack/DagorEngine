set(sources
  src/hb-blob.cc
  src/hb-buffer-serialize.cc
  src/hb-buffer.cc
  src/hb-draw.cc
  src/hb-common.cc
  src/hb-face.cc
  src/hb-font.cc
  src/hb-map.cc
  src/hb-ot-cff1-table.cc
  src/hb-ot-cff2-table.cc
  src/hb-ot-name.cc
  src/hb-ot-tag.cc
  src/hb-set.cc
  src/hb-shape.cc
  src/hb-shape-plan.cc
  src/hb-shaper.cc
  src/hb-static.cc
  src/hb-unicode.cc
  src/hb-ucd.cc
  src/hb-number.cc
  src/hb-fallback-shape.cc
  src/hb-aat-layout.cc
  src/hb-aat-map.cc
  src/hb-ot-face.cc
  src/hb-ot-font.cc
  src/hb-ot-metrics.cc
  src/hb-ot-layout.cc
  src/hb-ot-color.cc
  src/hb-ot-map.cc
  src/hb-ot-math.cc
  src/hb-ot-shape.cc
  src/hb-ot-shape-complex-arabic.cc
  src/hb-ot-shape-complex-default.cc
  src/hb-ot-shape-complex-hangul.cc
  src/hb-ot-shape-complex-hebrew.cc
  src/hb-ot-shape-complex-indic.cc
  src/hb-ot-shape-complex-indic-table.cc
  src/hb-ot-shape-complex-khmer.cc
  src/hb-ot-shape-complex-myanmar.cc
  src/hb-ot-shape-complex-thai.cc
  src/hb-ot-shape-complex-use.cc
  src/hb-ot-shape-complex-use-table.cc
  src/hb-ot-shape-complex-vowel-constraints.cc
  src/hb-ot-shape-normalize.cc
  src/hb-ot-shape-fallback.cc
  src/hb-ot-var.cc
  src/hb-ot-meta.cc
  src/hb-ft.cc
)
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/freetype/harfbuzz-2.6.4/src
  ${DAGOR_PROG_DIR}/3rdPartyLibs/freetype/freetype-2.8/include
)
set(defines __B_NO_MEM_BASE_INCLUDE _CRT_SECURE_NO_WARNINGS HAVE_FREETYPE HB_NO_GETENV HB_USE_ATEXIT)
if("${DAGOR_PLATFORM}-${DAGOR_ARCH}" STREQUAL "windows-x86_64")
  list(APPEND options -wd4267)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|linux)$")
  list(APPEND defines HAVE_PTHREAD)
endif()

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
)
