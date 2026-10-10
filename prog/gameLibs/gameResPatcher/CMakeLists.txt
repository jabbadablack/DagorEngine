# Patching of game resource packs (GRP/DxP), vromfs packs and sound banks, reusing unchanged data
set(sources resUpdUtil.cpp)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/engine)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
