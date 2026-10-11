# Ported from prog/gameLibs/render/antialiasing/jamfile (jam2cmake/skeleton.py; the mobile antialiasing of jam's UseMobileAA is not used)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources antialiasing.cpp temporalSuperResolution.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
