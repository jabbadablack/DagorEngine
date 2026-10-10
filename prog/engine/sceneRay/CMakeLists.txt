set(sources buildableSceneRay.cpp sceneray.cpp)
set(includes ${DAGOR_PROG_DIR}/engine/sharedInclude)
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$")
  list(APPEND options -Wno-undefined-bool-conversion)
endif()

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} COMPILE_OPTIONS ${options})
