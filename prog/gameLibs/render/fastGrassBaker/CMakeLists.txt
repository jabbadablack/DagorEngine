# Ported from prog/gameLibs/render/fastGrassBaker/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
# the baker on Windows outside Rel and IRel, the stub elsewhere
set(baker 0)
if(DAGOR_PLATFORM STREQUAL "windows")
  set(baker "$<NOT:$<CONFIG:Rel,IRel>>")
  dagor_use(3rdPartyLibs/image/tiff-4.4.0 3rdPartyLibs/convert/ispc_texcomp)
  set(deps "$<${baker}:3rdPartyLibs.image.tiff-4.4.0>" "$<${baker}:3rdPartyLibs.convert.ispc_texcomp>")
  list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/ispc_texcomp ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/gameLibs/rendInst)
endif()
set(dir ${CMAKE_CURRENT_SOURCE_DIR})
set(sources "$<IF:${baker},${dir}/fast_grass_baker.cpp,${dir}/fast_grass_baker_stub.cpp>")

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
