# Ported from prog/gameLibs/daSkies2/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR} shaders)
set(sources
  daStars.cpp
  daScattering.cpp
  daScatteringCPU.cpp
  daSkies.cpp
  daSkiesPanorama.cpp
  panoramaCompressor.cpp
  daSkiesToBlk.cpp
  daSkiesAstronomy.cpp
  daSkiesExporterConsole.cpp
  cloudsShaderVars.cpp
  cloudsField.cpp
  cloudsFormLUT.cpp
  cloudsLightRenderer.cpp
  cloudsRenderer.cpp
  cloudsRendererData.cpp
  cloudsShadows.cpp
  cloudsGenNoise.cpp
  cloudsGenWeather.cpp
  clouds2.cpp
)
list(APPEND deps engine/lib3d gameLibs/resourcePool)
if(DAGOR_GAME_RENDERER)
  list(APPEND deps gameLibs/render/nodeBasedShader)
else()
  list(APPEND deps gameLibs/render/nodeBasedShader/stub)
endif()
set(SourceES cloudsRainMapES.cpp.inl)
list(APPEND es_sources ${SourceES})

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} ES_SOURCES ${es_sources})
