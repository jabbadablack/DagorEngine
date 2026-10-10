# The game side of the common effects (light, sparks, modfx and compound effects of daFx; the effect list of
# prog/commonFx/fxList.jam). Flavor gz: with gravity zones (DAFX_USE_GRAVITY_ZONE), e.g. commonFx/commonFxGame:gz.
function(_commonFxGame flavor)
  set(defines)
  if(flavor STREQUAL "gz")
    set(defines DAFX_USE_GRAVITY_ZONE)
  elseif(flavor)
    message(FATAL_ERROR "commonFx/commonFxGame has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} STRICT
    SOURCES
      paramScriptsPool.cpp dafxSparksCpu.cpp dafxModFxSystem.cpp dafxSystemDesc.cpp dafxEmitterDebug.cpp
      modfx/modfx_cpu.cpp stub/outdatedFx.cpp commonFx.cpp
      lightFx.cpp dafxSparks.cpp dafxModFx.cpp dafxCompound.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/commonFx/commonFxGame ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    PRIVATE_DEFINES ${defines}
    DEPS gameLibs/daFx
  )
endfunction()

dagor_flavors(_commonFxGame)
