# Volumetric lights (VolumeLight) stubs for programs without volumetric lighting
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources volumetricLightsStub.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
