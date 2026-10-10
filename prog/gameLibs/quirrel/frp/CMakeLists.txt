# Quirrel FRP: observables (Watched, Computed) and their update graph, with an ImGui inspector
set(includes
  ${DAGOR_PROG_DIR}/engine/sharedInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
)
set(sources frp.cpp frp_imgui.cpp)
if(DAGOR_SQ_VAR_TRACE)
  list(APPEND defines SQ_VAR_TRACE_ENABLED)
endif()
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /wd4548)
endif()

dagor_add_library(STRICT
  QUIRREL
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
)
