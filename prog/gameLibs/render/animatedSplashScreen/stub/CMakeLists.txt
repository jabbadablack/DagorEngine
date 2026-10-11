# Ported from prog/gameLibs/render/animatedSplashScreen/stub/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/render/animatedSplashScreen/public_api)
set(sources animatedSplashScreenStub.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
