# ddsxCvt2: converts textures to DDSx with the asset manager's texture build settings (daKernel, the editor tree)
dagor_add_executable(ddsxCvt2 CONSOLE CDK
  SOURCES ddsxConverter2.cpp con_main.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/tools/sharedInclude ${DAGOR_PROG_DIR}/engine/sharedInclude
  DEPS engine/startup engine/math tools/libTools/dtx tools/libTools/assetMgr tools/libTools/assetMgrHlp
    tools/libTools/util tools/libTools/daKernel
)
