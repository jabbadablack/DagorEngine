# DAG file reading and writing: scene import, geometry mesh helpers, node trees, splines, textures, materials
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude)
set(sources
  impDagScene.cpp
  loadDagFile.cpp
  splineShape.cpp
  geomTreeFromDag.cpp
  geomMeshHelper.cpp
  geomMeshHelperImp.cpp
  geomMeshHelperMomj.cpp
  getDagTex.cpp
  dagFileExport.cpp
  dagUtil.cpp
  dagExporter.cpp
  dagCopy.cpp
  dagMatRemapUtil.cpp
)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
