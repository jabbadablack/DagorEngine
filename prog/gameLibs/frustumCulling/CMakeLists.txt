# Frustum planes as shader variables (set directly or by a scoped override)
set(sources frustumPlanes.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
