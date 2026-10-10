# The dynamic model renderer: per-instance render data of dynmodels and animchars for render contexts
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources dynmodelRenderer.cpp animCharRenderAdditionalData.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
