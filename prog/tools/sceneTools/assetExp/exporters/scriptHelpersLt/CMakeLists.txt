# The light script helpers of the effect exporters: curves, gradient boxes and the script GUI of the effect params
set(sources scriptCurves.cpp scriptGradientBox.cpp scriptGui.cpp scriptLoad.cpp)
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
