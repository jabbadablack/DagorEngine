# The asset manager's build helpers: the build caches of daBuild, its plugins' globals, texture conversion and asset
# references. Flavor emb: the build embedded in games (gameLibs/assets_import, _TARGET_EXPORTERS_STATIC).
function(_assetMgrHlp flavor)
  set(defines)
  if(flavor STREQUAL "emb")
    set(defines _TARGET_EXPORTERS_STATIC)
  elseif(flavor)
    message(FATAL_ERROR "tools/libTools/assetMgrHlp has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name}
    SOURCES assetBuildCache.cpp assetExpCache.cpp assetRefsCache.cpp daBuildPluginGlobals.cpp texConvCache.cpp
      texAssetBuilderTextureFactory.cpp reloadTexAsset.cpp refProviders.cpp assetLocalProps.cpp assetMgrHlp.cpp
      assetTags.cpp assetUtils.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude
    PRIVATE_DEFINES ${defines}
    DEPS 3rdPartyLibs/hash
  )
endfunction()

dagor_flavors(_assetMgrHlp)
