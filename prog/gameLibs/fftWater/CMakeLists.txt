# Ported from prog/gameLibs/fftWater/jamfile (jam2cmake/skeleton.py)
set(sources
  wake.cpp
  waterRenderCommon.cpp
  waterRender.cpp
  cpuTexSampler.cpp
  chopWaterRender.cpp
  chopWaterPhysics.cpp
  chopWaterGen.cpp
  waterRenderGpGPU.cpp
  waterRenderCSGPU.cpp
  gpuFetch.cpp
  waterPhys.cpp
  fftWater.cpp
  fftWaterUtils.cpp
  distanceField.cpp
  flowMap.cpp
  waterCommon.cpp
  fftCPU/FFT_CPU_Simulation.cpp
)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/gameLibs/fftWater/fftCPU)
set(deps gameLibs/heightmap engine/lib3d)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
