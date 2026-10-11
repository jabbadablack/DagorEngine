# Ported from prog/1stPartyLibs/daScript/modules/dasImgui/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/imgui
  ${DAGOR_PROG_DIR}/3rdPartyLibs/imgui-node-editor
)
set(AllSrcFolder_CPP src)
dagor_glob_sources(sources DIRS ${AllSrcFolder_CPP} GLOB *.cpp)
list(APPEND deps 3rdPartyLibs/eastl 1stPartyLibs/daScript 3rdPartyLibs/imgui 3rdPartyLibs/imgui-node-editor)
if(DAGOR_DAS_AOT)
  list(APPEND deps 1stPartyLibs/daScript/modules/dasImgui/daslib) # its daslib scripts, compiled ahead of time
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
