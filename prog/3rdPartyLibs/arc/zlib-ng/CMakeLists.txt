# zlib-ng in zlib-compatible mode, with the SIMD paths of the target
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng)
set(sources
  adler32.c
  chunkset.c
  compare256.c
  compress.c
  cpu_features.c
  crc32.c
  crc32_comb.c
  crc32_fold.c
  deflate.c
  deflate_fast.c
  deflate_huff.c
  deflate_medium.c
  deflate_quick.c
  deflate_rle.c
  deflate_slow.c
  deflate_stored.c
  functable.c
  gzlib.c
  gzread.c
  gzwrite.c
  infback.c
  inffast.c
  inflate.c
  inftrees.c
  insert_string.c
  insert_string_roll.c
  slide_hash.c
  trees.c
  uncompr.c
  zutil.c
)
set(Allx86Sources
  adler32_ssse3.c
  chunkset_sse2.c
  compare256_sse2.c
  crc32_fold_pclmulqdq.c
  crc32_fold_vpclmulqdq.c
  insert_string_sse42.c
  slide_hash_sse2.c
  x86_features.c
)
set(AllAVX2Sources slide_hash_avx2.c chunkset_avx.c compare256_avx2.c adler32_avx2.c)
set(AllNEONSources adler32_neon.c arm_features.c chunkset_neon.c slide_hash_neon.c)
set(AllACLESources crc32_acle.c insert_string_acle.c)
set(MacX86Sources chunkset_sse2.c compare256_sse2.c slide_hash_sse2.c x86_features.c)
list(APPEND c_options -DZLIB_COMPAT)
if(DAGOR_PLATFORM MATCHES "^(linux|windows)$")
  if(DAGOR_ARCH STREQUAL "x86_64")
    set(_Allx86Sources_1 ${Allx86Sources})
    list(TRANSFORM _Allx86Sources_1 PREPEND "arch/x86/")
    list(APPEND sources ${_Allx86Sources_1})
    list(APPEND c_options -DX86_FEATURES -DX86_SSE2 -DX86_SSE2_CHUNKSET -DX86_SSE2_SLIDEHASH)
  elseif(DAGOR_ARCH STREQUAL "arm64")
    list(APPEND c_options
      -DARM_FEATURES
      -DARM_NEON_SLIDEHASH
      -DARM_NEON_CHUNKSET
      -DARM_NEON_ADLER32
      -DARM_NEON_HASLD4
    )
    set(_AllNEONSources_2 ${AllNEONSources})
    list(TRANSFORM _AllNEONSources_2 PREPEND "arch/arm/")
    list(APPEND sources ${_AllNEONSources_2})
  endif()
  if("${DAGOR_PLATFORM}-${DAGOR_ARCH}" STREQUAL "windows-x86_64")
    list(APPEND c_options -wd4267)
  endif()
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  if(DAGOR_ARCH STREQUAL "x86_64")
    set(_MacX86Sources_3 ${MacX86Sources})
    list(TRANSFORM _MacX86Sources_3 PREPEND "arch/x86/")
    list(APPEND sources ${_MacX86Sources_3})
    list(APPEND c_options -DX86_FEATURES -DX86_SSE2 -DX86_SSE2_CHUNKSET -DX86_SSE2_SLIDEHASH)
  elseif(DAGOR_ARCH STREQUAL "arm64")
    list(APPEND c_options
      -DARM_FEATURES
      -DARM_NEON_SLIDEHASH
      -DARM_NEON_CHUNKSET
      -DARM_NEON_ADLER32
      -DARM_NEON_HASLD4
    )
    set(_AllNEONSources_4 ${AllNEONSources})
    list(TRANSFORM _AllNEONSources_4 PREPEND "arch/arm/")
    list(APPEND sources ${_AllNEONSources_4})
  endif()
endif()
if(DAGOR_ARCH MATCHES "^(e2k|x86_64)$")
  list(APPEND c_options -DX86_SSSE3)
endif()
if(DAGOR_PLATFORM MATCHES "^(android|iOS)$")
  set(_AllNEONSources_5 ${AllNEONSources})
  list(TRANSFORM _AllNEONSources_5 PREPEND "arch/arm/")
  list(APPEND sources ${_AllNEONSources_5})
  list(APPEND c_options
    -DARM_FEATURES
    -DARM_NEON_SLIDEHASH
    -DARM_NEON_CHUNKSET
    -DARM_NEON_ADLER32
    -DARM_NEON_HASLD4
  )
endif()
list(APPEND force_includes supp/dag_null.h)

dagor_add_library(SOURCES ${sources}
  FORCE_INCLUDES ${force_includes}
  PRIVATE_INCLUDES ${includes}
  C_OPTIONS ${c_options}
)
