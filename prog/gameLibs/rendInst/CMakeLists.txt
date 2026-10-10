# Render instances: generated and placed instances (rendinst cells, extra instances, impostors, destruction), their
# collision, visibility and rendering. Dedicated servers (DAGOR_DEDICATED) have no impostor textures.
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources
  dumpCollisions.cpp
  dumpScenes.cpp
  rendInstAccess.cpp
  rendInstExtraAccess.cpp
  rendInstCommon.cpp
  rendInstGen.cpp
  rendInstGenLand.cpp
  rendInstGenCollision.cpp
  rendInstGenExtra.cpp
  rendInstExtraAdditionalData.cpp
  rendInstGenExtraMaxHeight.cpp
  rendInstGenDebris.cpp
  rendInstGenGlobals.cpp
  rendInstRotationPalette.cpp
  rendInstGenRtTools.cpp
  rendInstUtil.cpp
  rendInstStubRes.cpp
  rendInstDesc.cpp
  riGrid.cpp
  riGridDebug.cpp
  riGridDump.cpp
  treeDestr.cpp
  riexSync.cpp
  render/clipmapShadow.cpp
  render/gpuObjects.cpp
  render/genRender.cpp
  render/impostor.cpp
  render/extraRender.cpp
  render/clipShadows.cpp
  render/depthShadows.cpp
  render/riShaderConstBuffers.cpp
  render/extra/consoleHandler.cpp
  render/riGenRenderer.cpp
  visibility/genVisibility.cpp
  visibility/extraVisibility.cpp
  debug/collisionVisualization.cpp
  debug/rendinstRulerDebug.cpp
)
if(DAGOR_DEDICATED)
  list(APPEND sources stub/impostorTextureMgr.cpp)
else()
  list(APPEND sources impostorTextureMgr.cpp)
endif()
set(defines VECMATH_NO_FMA) # v_madd on NEON is explicit vfmaq that ignores ffp-contract=off
if(DAGOR_BUILDING_TOOLS)
  list(APPEND defines _TARGET_PC_TOOLS_BUILD)
endif()
set(deps
  gameLibs/render/texcompressors
  gameLibs/render/primitiveObjects
  gameLibs/render/debug3dSolid
  gameLibs/render/pointLod
  engine/lib3d
  engine/libFx
  engine/consoleProc
  3rdPartyLibs/regExp
  gameLibs/gpuObjects
  gameLibs/gameMath
  gameLibs/landMesh/rendinstIntegration
  gameLibs/resourcePool
)
# the debug mesh rendering outside Rel
dagor_use(gameLibs/render/debugMesh gameLibs/render/debugMesh/stub)
list(APPEND deps "$<IF:$<CONFIG:Rel>,gameLibs.render.debugMesh.stub,gameLibs.render.debugMesh>")
set(options)
if(DAGOR_CC MATCHES "^(clang|clang-cl|gcc)$")
  # no fused multiply-adds: the generated positions must match on every platform (contract=off alone does not stop
  # the backend from fusing under fast-math)
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
  list(APPEND options ${xclang}fno-unsafe-math-optimizations ${xclang}ffp-contract=off)
  if(DAGOR_ARCH STREQUAL "x86_64")
    list(APPEND options ${xclang}mno-fma)
  endif()
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
)
