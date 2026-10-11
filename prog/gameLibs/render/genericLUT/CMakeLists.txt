# Ported from prog/gameLibs/render/genericLUT/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources genericLUT.cpp commonLUT.cpp colorGradingLUT.cpp fullColorGradingLUT.cpp dynamicLUT.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
