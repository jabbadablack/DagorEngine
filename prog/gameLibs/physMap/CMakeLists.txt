# Physical material maps: a bitmap of material ids over the land with decal meshes, their loading and compact decals
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources physMap.cpp physMatHtTex.cpp physMapLoad.cpp physMapCompactDecals.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
