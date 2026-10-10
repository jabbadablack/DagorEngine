# Math: vectors and matrices, frustums, geometry queries, noise, DXT decompression. Flavor pm<N>[-<frames>]
# (engine/math:pm1-1000) is built with MEASURE_PERF=<N> and MEASURE_PERF_FRAMES=<frames>, for the profiling builds.
function(_engine_math flavor)
  set(sources
    convexHullComputer.cpp
    half.cpp
    calc_occluder.cpp
    colorMatrix.cpp
    boundingSphere.cpp
    math3d.cpp
    math2d.cpp
    frustum.cpp
    mathAng.cpp
    perlin.cpp
    ffd44.cpp
    triangleTriangleIntersection.cpp
    sHmath.cpp
    geomTree.cpp
    geomTreeMap.cpp
    mesh.cpp
    mathUtils.cpp
    kaiserSimd.cpp
    imageFunctions.cpp
    polyUtils.cpp
    capsuleTriangle.cpp
    wooray2d.cpp
    wooray3d.cpp
    checkNanTest.cpp
    sdf_edt.cpp
  )
  if(DAGOR_ARCH STREQUAL "x86_64")
    list(APPEND sources dxtDecompressSimd.cpp)
  else()
    list(APPEND sources dxtDecompress.cpp)
  endif()
  set(defines)
  if(DAGOR_KERNEL_LINKAGE STREQUAL "static")
    list(APPEND sources rndSeed.cpp gaussTbl.cpp)
  elseif(DAGOR_PLATFORM STREQUAL "windows")
    list(APPEND defines _DEBUG_TAB_)
  endif()

  set(flavor_defines)
  if(flavor MATCHES "^pm([0-9]+)(-([0-9]+))?$")
    list(APPEND flavor_defines MEASURE_PERF=${CMAKE_MATCH_1} MEASURE_PERF_FRAMES=${CMAKE_MATCH_3})
  elseif(NOT flavor STREQUAL "")
    message(FATAL_ERROR "engine/math has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} STRICT SOURCES ${sources} PRIVATE_DEFINES ${defines} ${flavor_defines} DEPS 3rdPartyLibs/eastl)
endfunction()

dagor_flavors(_engine_math)
