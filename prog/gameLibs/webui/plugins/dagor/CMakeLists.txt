# Ported from prog/gameLibs/webui/plugins/dagor/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/webui
  ${DAGOR_PROG_DIR}/dagorInclude
)
set(sources dagorplugins.cpp)
list(APPEND stringify_array showMemFlameGraph.html)
if(DAGOR_BUILDING_TOOLS)
  list(APPEND defines _TARGET_PC_TOOLS_BUILD)
else()
  list(APPEND sources memmap.cpp)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  STRINGIFY_ARRAY ${stringify_array}
)
