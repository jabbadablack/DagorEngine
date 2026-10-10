# 2D rectangle bin packing (Guillotine, MaxRects, Skyline, PowerOfTwo), e.g. for texture atlases
set(includes include)
set(sources src/GuillotineBinPack.cpp src/MaxRectsBinPack.cpp src/SkylineBinPack.cpp src/PowerOfTwoBinPack.cpp)
list(APPEND deps 3rdPartyLibs/eastl)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND options -Wno-unused-parameter)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options} DEPS ${deps})
