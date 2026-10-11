# Ported from prog/gameLibs/billboardDecals/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${CMAKE_CURRENT_SOURCE_DIR})
set(sources billboardDecals.cpp matProps.cpp)
list(APPEND deps engine/lib3d gameLibs/decalMatrices)
if(IS_DIRECTORY "${DAGOR_PROG_DIR}/gameLibs/propsRegistry")
  list(APPEND defines HAS_PROPS_REGISTRY)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines} DEPS ${deps})
