# The land mesh (heightmap terrain with clipmap texturing, micro details and the weight atlas); its clipmap debug UI
# (ImGui) in Dev and Dbg
set(sources
  landMicroDetails.cpp
  lmeshManager.cpp
  lmeshWeightAtlas.cpp
  lmeshWeightAtlasGpu.cpp
  lmeshWeightAtlasLegacyCpu.cpp
  lmeshWeightAtlasLegacyGpu.cpp
  lmeshLandClasses.cpp
  lmeshRenderer.cpp
  lmeshRenderingModeState.cpp
  lmeshRendererLandClasses.cpp
  virtualtexture.cpp
  landRayTracerSoA4.cpp
  lmeshRendererGlue.cpp
  lastClip.cpp
  biomeQuery.cpp
  heightmapQuery.cpp
  lmeshMirroring.cpp
  lmeshHoles.cpp
)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/gamePhys/collision
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/engine/lib3d
  ${DAGOR_PROG_DIR}/3rdPartyLibs
)
set(deps
  gameLibs/landMesh/rendinstIntegration
  gameLibs/heightmap
  gameLibs/physMap
  3rdPartyLibs/eastl
  engine/daBVH
  3rdPartyLibs/convert/fastDXT
)
set(dir "${CMAKE_CURRENT_SOURCE_DIR}")
set(debug "$<CONFIG:Dev,Dbg>")
list(APPEND sources "$<IF:${debug},${dir}/clipmapDebug.cpp,${dir}/clipmapDebugStub.cpp>")
dagor_use(3rdPartyLibs/imgui engine/imgui)
list(APPEND deps "$<${debug}:3rdPartyLibs.imgui>" "$<${debug}:engine.imgui>")
set(options)
if(DAGOR_CC MATCHES "^(clang|clang-cl|gcc)$")
  # no fused multiply-adds and no unsafe math: the land heights must match on every platform
  set(xclang -)
  if(DAGOR_CC STREQUAL "clang-cl")
    set(xclang /clang:-)
  endif()
  if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
    list(APPEND options -Wno-overriding-option)
  endif()
  if(DAGOR_PLATFORM MATCHES "^(iOS|linux|macOS)$")
    list(APPEND options -Wno-overriding-t-option)
  endif()
  list(APPEND options ${xclang}fno-unsafe-math-optimizations ${xclang}fno-trapping-math ${xclang}ffp-contract=off)
  if(DAGOR_ARCH STREQUAL "x86_64")
    list(APPEND options ${xclang}mno-fma)
  endif()
endif()
list(APPEND defines VECMATH_NO_FMA) # v_madd on NEON is explicit vfmaq that ignores ffp-contract=off

dagor_add_library(SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
