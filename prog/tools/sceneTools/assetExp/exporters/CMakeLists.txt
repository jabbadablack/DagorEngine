# The exporters of daBuild, one plugin per asset type: animations (a2dExp), anim chars, collision, fast physics, effects,
# impostors, land classes, local shaders, materials, models (rendinsts, dynamic models, skeletons, grass), physics
# objects and textures. (jam's static exporters library is for the static daBuild, which no build uses.)
include(../dabuildPlugin.cmake)
set(shared ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(editor ${DAGOR_PROG_DIR}/tools/sceneTools/daEditorX/include)
set(images 3rdPartyLibs/image/avif 3rdPartyLibs/image/jpeg-6b 3rdPartyLibs/image/psdRead 3rdPartyLibs/image/tiff-4.4.0
  3rdPartyLibs/image/libpng-1.4.22 3rdPartyLibs/arc/zlib-ng)

dabuild_plugin(a2dExp
  SOURCES a2dExp.cpp a2dOptimizer.cpp exp_skeleton_tools.cpp exp_tools.cpp
  PRIVATE_INCLUDES ${shared} ${DAGOR_PROG_DIR}/3rdPartyLibs/acl/includes
  DEPS engine/startup tools/libTools/assetMgr engine/math engine/lib3d engine/drv/drv3d_null
    tools/libTools/shaderResBuilder tools/libTools/dagFileRW)
dabuild_plugin(animCharExp
  SOURCES animCharExp.cpp exp_animTree.cpp exp_stateGraph.cpp exp_animChar.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math engine/perfMon tools/libTools/assetMgr tools/libTools/pageAsg engine/lib3d
    engine/shaders engine/sceneRay engine/gameRes engine/scene engine/drv/drv3d_null tools/libTools/shaderResBuilder
    tools/libTools/dagFileRW tools/libTools/ambientOcclusion)
dabuild_plugin(collisionExp
  SOURCES exp_tools.cpp exp_collision.cpp
  PRIVATE_INCLUDES ${shared} ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    ${DAGOR_PROG_DIR}/3rdPartyLibs/math/vhacd
  DEPS engine/startup engine/math engine/lib3d engine/drv/drv3d_null engine/gameRes engine/sceneRay engine/scene
    engine/coreUtil tools/libTools/assetMgr tools/libTools/dagFileRW tools/libTools/math tools/libTools/collision
    3rdPartyLibs/math/vhacd)
dabuild_plugin(fastPhysExp
  SOURCES fastPhysExp.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math engine/perfMon tools/libTools/assetMgr tools/libTools/fastPhysData
    tools/libTools/dagFileRW)
dabuild_plugin(fxExp
  SOURCES fxExp.cpp fxExpStubs.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math engine/lib3d engine/drv/drv3d_null engine/consoleProc tools/libTools/assetMgr
    tools/libTools/dagFileRW tools/sceneTools/assetExp/exporters/scriptHelpersLt commonFx/commonFxTools
    3rdPartyLibs/math/srcc_msu)
dabuild_plugin(impostorExp
  SOURCES exp_impostorData.cpp
  PRIVATE_INCLUDES ${shared} ${editor}
  DEPS engine/startup tools/libTools/assetMgr)
dabuild_plugin(landClsExp
  SOURCES landClsExp.cpp landClsExpStubs.cpp
  PRIVATE_INCLUDES ${shared} ${editor}
  DEPS engine/startup engine/image 3rdPartyLibs/hash tools/libTools/assetMgr
    tools/sceneTools/daEditorX/services/bitMaskMgr)
dabuild_plugin(locShadersExp
  SOURCES locShadersExp.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math tools/libTools/assetMgr)
dabuild_plugin(matExp
  SOURCES matExp.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math engine/lib3d tools/libTools/assetMgr tools/libTools/dagFileRW)
dabuild_plugin(modelExp
  SOURCES modelExp.cpp modelExpUtil.cpp exp_tools.cpp exp_skeleton_tools.cpp exp_rendInst.cpp exp_dynModel.cpp
    exp_skeleton.cpp exp_rndGrass.cpp
  PRIVATE_INCLUDES ${shared} ${DAGOR_PROG_DIR}/engine/sharedInclude
  PRIVATE_DEFINES _DEBUG_TAB_
  DEPS engine/startup engine/math engine/lib3d engine/shaders engine/drv/drv3d_null engine/sceneRay engine/gameRes
    engine/scene engine/perfMon tools/libTools/assetMgr tools/libTools/shaderResBuilder tools/libTools/dagFileRW
    engine/image tools/libTools/ambientOcclusion ${images})
dabuild_plugin(phObjExp
  SOURCES phObjExp.cpp phSysObj.cpp
  PRIVATE_INCLUDES ${shared}
  DEPS engine/startup engine/math engine/lib3d engine/drv/drv3d_null tools/libTools/assetMgr tools/libTools/dagFileRW)
# textures: the DDSx conversion of every format, ASTC through the astcenc programs next to the tools, BC/ETC through
# the ISPC texture compressor
set(tex_includes ${shared} ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/nvtt-2.0.7 ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(tex_defines)
set(tex_deps engine/startup engine/image engine/math tools/libTools/assetMgr 3rdPartyLibs/convert/nvtt-2.0.7 ${images}
  3rdPartyLibs/eastl)
if(DAGOR_ARCH STREQUAL "e2k")
  set(tex_defines TEX_CANNOT_USE_ISPC)
else()
  list(APPEND tex_includes ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/ispc_texcomp)
  list(APPEND tex_deps 3rdPartyLibs/convert/ispc_texcomp)
endif()
dabuild_plugin(texExp
  SOURCES texExp.cpp
  PRIVATE_INCLUDES ${tex_includes}
  PRIVATE_DEFINES ${tex_defines}
  DEPS ${tex_deps})
dagor_require_sdk(astcenc)
dagor_runtime_files(texExp SUBDIR ../.. FILES ${DAGOR_SDK_ASTCENC_RUNTIME})
