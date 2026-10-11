# Ported from prog/gameLibs/render/levelProfiler/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/rendInst
  ${DAGOR_PROG_DIR}/gameLibs/render/levelProfiler/include
  ${DAGOR_PROG_DIR}/gameLibs/render/levelProfiler/include/dataModules
  ${DAGOR_PROG_DIR}/gameLibs/render/levelProfiler/include/uiComponents
  ${DAGOR_PROG_DIR}/gameLibs/render/levelProfiler/include/uiModules
)
# the profiler outside Rel, the stub in Rel
set(sources levelProfiler.cpp src/levelProfilerExporter.cpp src/levelProfilerUI.cpp src/dataModules/textureModule.cpp
  src/dataModules/riModule.cpp src/uiComponents/levelProfilerTableBase.cpp src/uiComponents/levelProfilerWidgets.cpp
  src/uiComponents/levelProfilerFilter.cpp src/uiModules/levelProfilerTextureTable.cpp
  src/uiModules/levelProfilerRiTable.cpp)
list(TRANSFORM sources REPLACE "^(.+)$" "$<$<NOT:$<CONFIG:Rel>>:${CMAKE_CURRENT_SOURCE_DIR}/\\1>")
list(APPEND sources "$<$<CONFIG:Rel>:${CMAKE_CURRENT_SOURCE_DIR}/levelProfilerStub.cpp>")

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes})
