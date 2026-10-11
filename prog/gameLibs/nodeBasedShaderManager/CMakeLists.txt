# Ported from prog/gameLibs/nodeBasedShaderManager/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources nodeBasedShaderManager.cpp)
# the shaders' compilation where the games have webui on Windows (prog/daNetGame/setup.jam), the stub elsewhere
set(compile 0)
if(DAGOR_PLATFORM STREQUAL "windows" AND DEFINED DAGOR_GAME_WEBUI AND DAGOR_VARIANT STREQUAL "game")
  set(compile "${DAGOR_GAME_WEBUI}")
endif()
set(dir ${CMAKE_CURRENT_SOURCE_DIR})
list(APPEND sources "$<IF:${compile},${dir}/nodeBasedShaderManagerCompile.cpp,${dir}/stub/nodeBasedShaderManagerCompileStub.cpp>")

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
