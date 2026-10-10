# The web UI's node-based shader editors (environment cover, fog, clouds). Flavor comp: the compile-only build of the
# node-based shader compiler (NBSM_COMPILE_ONLY), e.g. gameLibs/webui/plugins/shaderEditors:comp.
function(_shaderEditors flavor)
  set(defines)
  if(flavor STREQUAL "comp")
    set(defines NBSM_COMPILE_ONLY)
  elseif(flavor)
    message(FATAL_ERROR "gameLibs/webui/plugins/shaderEditors has no flavor '${flavor}'")
  endif()
  dagor_flavor_target("${flavor}" name)
  dagor_add_library(${name} STRICT
    SOURCES shaderEditors.cpp enviCoverShaderEditor.cpp fogShaderEditor.cpp cloudsShaderEditor.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude
    PRIVATE_DEFINES ${defines}
  )
endfunction()

dagor_flavors(_shaderEditors)
