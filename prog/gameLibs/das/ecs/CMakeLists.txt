# daScript modules of the games (prog/gameLibs/das/common.jam): pull.cpp references them; with DAGOR_DAS_AOT their
# scripts are compiled into the library
dagor_glob_sources(das DIRS . GLOB *.das)
set(defines)
if(DAGOR_DAS_AOT)
  set(defines BUILD_AOT_LIB) # pull.cpp then names the AOT pull
endif()
dagor_add_library(QUIRREL
  SOURCES pull.cpp
  PRIVATE_DEFINES ${defines}
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/modules/dasQuirrel/src
  DAS_AOT ${das} DAS_AOT_PULL ecs_aot_DAS_pull_AOT
)
