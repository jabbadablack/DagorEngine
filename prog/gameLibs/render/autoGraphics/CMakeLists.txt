# Ported from prog/gameLibs/render/autoGraphics/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
if(DAGOR_PLATFORM MATCHES "^(linux|windows)$")
  set(sources
    cpuBenchmark.cpp
    autoQualityPreset.cpp
    gpuDatabase/sampler.cpp
    presetDatabase/sampler.cpp
    autoResolution.cpp
    autoAntialiasing.cpp
  )
else()
  set(sources cpuBenchmarkStub.cpp autoGraphicsStub.cpp)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
