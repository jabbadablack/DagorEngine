# Ported from prog/gameLibs/daFracture/render/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources renderContext.cpp renderList.cpp renderMesh.cpp unitedGeomBuffers.cpp material.cpp sceneRender.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
