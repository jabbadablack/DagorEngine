# dabuild_plugin(<name> <dagor_add_shared_library arguments>...): a daBuild plugin (an exporter or reference
# provider) in plugins/dabuild of the CDK, on daKernel with the asset manager helpers (jam's
# dabuild_plugin_common.jam); included by the plugins' directories
include_guard(GLOBAL)
function(dabuild_plugin name)
  dagor_add_shared_library(${name} CDK_SUBDIR plugins/dabuild
    OUTPUT_DIR ${CMAKE_BINARY_DIR}/bin/plugins/dabuild
    ${ARGN}
    DEPS tools/libTools/assetMgrHlp tools/libTools/util tools/libTools/daKernel
  )
endfunction()
