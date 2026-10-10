# The shader system: bindumps, shader variables and blocks, materials, shader meshes, scenes, render states.
#
# The shader variables come from engine.shaders.vars (the bindump's) or, in programs that set the DAGOR_SHADER_VARS
# target property, from a mock (mock: tests of render code) or a stub (stub); see dagor_add_link_select().
set(sources
  shaderVariableInfo.cpp
  bindumpReloadListener.cpp
  overrideStates.cpp
  renderStates.cpp
  shadersBinaryDataDbg2.cpp
  shaderBlock.cpp
  globVarsBlk.cpp
  postFxRenderer.cpp
  shStateBlk.cpp
  shStateBlkClose.cpp
  shStateBlkData.cpp
  shaders_globdata.cpp
  scene_binload.cpp
  shaderMesh.cpp
  shaderMeshSimple.cpp
  shaderResUnitedData.cpp
  atlasBlockManager.cpp
  shUtils.cpp
  shUtilsEx.cpp
  dynamicShaderHelper.cpp
  dynamicShadersBuffer.cpp
  dynShaderBuf.cpp
  debugPrimitivesVbuffer.cpp
  scene.cpp
  scene_vis.cpp
  shadersBinaryDataLoad.cpp
  shadersBinaryDataDbg.cpp
  shadersDbg.cpp
  shadersCon.cpp
  scriptSElem.cpp
  scriptSMat.cpp
  shaders.cpp
  shadersRes.cpp
  shFunc.cpp
  shSkinnedMesh.cpp
  dynSceneRes.cpp
  rendInstRes.cpp
  instShaderMeshRes.cpp
  matVdata.cpp
  matVdataLoad.cpp
  voxelSurfaceData.cpp
  shaderMeshTexLoadCtrl.cpp
  computeShaders.cpp
  meshShaders.cpp
  sh_vars.cpp
  refinedBlock.cpp
  refinedBlockExec.cpp
  shMaterialUtils.cpp
  shStateBlockBindless.cpp
  shStateBlockSlotTextures.cpp
  shAssert.cpp
  shBindumps.cpp
  bindposeBufferManager.cpp
)
set(defines)
if(DAGOR_BUILDING_TOOLS)
  list(APPEND defines SHADERS_ALLOW_2_BINDUMP)
endif()
set(stcode ${DAGOR_CPP_STCODE})
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64" AND NOT DAGOR_SSE EQUAL 4)
  set(stcode disable)
endif()
if(stcode MATCHES "^(enable|both|validate)$")
  list(APPEND sources stcode.cpp stcode/stcodeCallbacksImpl.cpp)
  list(APPEND defines CPP_STCODE)
  if(stcode STREQUAL "validate")
    list(APPEND sources stcode/compareStcode.cpp)
    list(APPEND defines VALIDATE_CPP_STCODE)
  endif()
  if(DAGOR_CPP_STCODE_BRANCHED)
    list(APPEND defines CPP_STCODE_DYNAMIC_BRANCHING)
  endif()
endif()
if(DAGOR_SHADERS_CAM_STUB)
  list(APPEND defines CAM_STUB)
endif()
if(DAGOR_PROFILE_STCODE)
  list(APPEND sources profileStcode.cpp)
  list(APPEND defines PROFILE_STCODE)
endif()
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

foreach(vars vars varsMock varsStub)
  string(REPLACE "vars" "shadersBinaryDataVars" source "${vars}")
  dagor_add_library(engine.shaders.${vars} SOURCES ${source}.cpp PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines})
endforeach()
dagor_add_link_select(engine.shaders.variables PROPERTY DAGOR_SHADER_VARS DEFAULT engine.shaders.vars
  mock engine.shaders.varsMock stub engine.shaders.varsStub)

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  DEPS engine.shaders.variables 3rdPartyLibs/eastl 3rdPartyLibs/meshoptimizer 3rdPartyLibs/hash/BLAKE3
)
