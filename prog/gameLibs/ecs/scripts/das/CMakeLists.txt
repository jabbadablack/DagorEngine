# daECS bindings of daScript: entity systems, events and queries in scripts
set(includes
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/engine/dagorInclude
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
)
file(GLOB AllSources RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")
set(sources ${AllSources})
if(DAGOR_DAS_LLVM_AOT)
  list(APPEND defines DAS_LLVM_AOT)
endif()
set(SourceDAS ecs.das)
list(APPEND stringify ${SourceDAS})
list(APPEND deps 1stPartyLibs/daScript engine/workCycle)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND options /bigobj)
endif()
if(IS_DIRECTORY "${DAGOR_PROG_DIR}/engine/daECS/net")
  list(APPEND defines HAS_DANET)
endif()

dagor_add_library(STRICT
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
  DEPS ${deps}
  STRINGIFY ${stringify}
)
