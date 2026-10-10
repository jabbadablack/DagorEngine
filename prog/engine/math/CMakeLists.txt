# Math: vectors and matrices, frustums, geometry queries, noise, DXT decompression. Programs with the
# DAGOR_MEASURE_PERF property get the build with profiling counters (MEASURE_PERF=1), as AssetViewer.
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

foreach(build standard measurePerf)
  set(build_defines ${defines})
  if(build STREQUAL "measurePerf")
    list(APPEND build_defines MEASURE_PERF=1)
  endif()
  dagor_add_library(engine.math.${build} STRICT SOURCES ${sources} PRIVATE_DEFINES ${build_defines}
    DEPS 3rdPartyLibs/eastl)
endforeach()
dagor_add_link_choice(engine.math PROPERTY DAGOR_MEASURE_PERF ON engine.math.measurePerf OFF engine.math.standard)
