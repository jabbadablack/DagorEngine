# Physics resources (bodies and helpers), physics counters and twist controllers, common to the physics libraries
set(sources physResource.cpp physStat.cpp physTwistCtrl.cpp)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
