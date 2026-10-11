# Ported from prog/gameLibs/render/animatedSplashScreen/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/render/animatedSplashScreen/public_api
  ${DAGOR_PROG_DIR}/gameLibs/render/animatedSplashScreen/graph
)
set(sources animatedSplashScreen.cpp)
set(deps
  gameLibs/render
  gameLibs/render/hdrRender
  gameLibs/render/shaderCacheWarmup
  gameLibs/render/antialiasing
  gameLibs/render/animatedSplashScreen/graph
)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
