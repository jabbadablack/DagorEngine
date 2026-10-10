# Fast physics editor data: points, bones, clippers and actions, and their export
set(includes ${DAGOR_PROG_DIR}/tools/sharedInclude)
set(sources fp_edActions.cpp fp_edbone.cpp fp_edclipper.cpp fp_edpoint.cpp fp_export.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
