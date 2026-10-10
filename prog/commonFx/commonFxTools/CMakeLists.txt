# The tool side of the common effects (their editor classes and the effect list of prog/commonFx/fxList.jam), for the
# effect exporter and the editors. Flavor emb: the build embedded in games (_TARGET_EXPORTERS_STATIC).
function(_commonFxTools flavor)
  set(defines)
  if(flavor STREQUAL "emb")
    set(defines _TARGET_EXPORTERS_STATIC)
  elseif(flavor)
    message(FATAL_ERROR "commonFx/commonFxTools has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name}
    SOURCES effectClassTools.cpp commonFxTools.cpp outdatedFxTools.cpp dafxEmitter_tools.cpp lightfxShadow_tools.cpp
      lightFx_tools.cpp dafxSparks_tools.cpp dafxModFx_tools.cpp dafxCompound_tools.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/commonFx/commonFxGame
    PRIVATE_DEFINES ${defines}
  )
endfunction()

dagor_flavors(_commonFxTools)
