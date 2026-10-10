# daBuild, the asset build of the content pipeline: daBuild (the program), daBuild-job (its worker processes) and the
# daBuild library that the editors load, all on daKernel (the editor tree, DAGOR_KERNEL_LINKAGE dynamic). The exporters
# and reference providers are plugins (exporters/, refProviders/, plugins/dabuild of the CDK).
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  message(FATAL_ERROR "tools/sceneTools/assetExp is built on daKernel: configure the editor tree")
endif()
if(DAGOR_SANITIZE STREQUAL "address")
  message(FATAL_ERROR "daBuild is built on daKernel, which ASan does not support")
endif()
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/engine)
set(export_sources loadPlugins.cpp texExport.cpp resExport.cpp daBuild.cpp assetExport.cpp jobPool.cpp)
set(program_deps
  engine/startup
  engine/math
  engine/gameRes
  engine/lib3d
  engine/drv/drv3d_null
  engine/perfMon/daProfilerStub
  tools/libTools/assetMgr
  tools/libTools/assetMgrHlp
  tools/libTools/util
  tools/libTools/dtx
  3rdPartyLibs/hash
  tools/libTools/daKernel
)
if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
  list(APPEND program_deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(daBuild CONSOLE CDK
  SOURCES cmain.cpp ${export_sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES _TARGET_DABUILD_STATIC
  DEPS ${program_deps}
)
dagor_add_executable(daBuild-job CONSOLE CDK
  SOURCES cmain-job.cpp ${export_sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES _TARGET_DABUILD_STATIC
  DEPS ${program_deps} 3rdPartyLibs/arc/zlib-ng
)
# the library of the editors (named daBuild too; its debug info is daBuild-dll.pdb, as jam named it)
dagor_add_shared_library(daBuildLib CDK OUTPUT_NAME daBuild
  SOURCES ${export_sources}
  PRIVATE_INCLUDES ${includes}
  DEPS engine/startup engine/math tools/libTools/assetMgr tools/libTools/assetMgrHlp tools/libTools/util
    tools/libTools/dtx 3rdPartyLibs/arc/zlib-ng 3rdPartyLibs/hash tools/libTools/daKernel
  PROPERTIES PDB_NAME daBuild-dll
)
