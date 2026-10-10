# Tools math: k-DOP bounding volumes
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources kdop.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
