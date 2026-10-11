# The game: the client, or the dedicated server in a tree with DAGOR_DEDICATED (the *-dedicated presets), into
# game/<platform>-<arch>
dagor_glob_sources(das DIRS scripts/dng_empty scripts/dng_empty/es GLOB *.das) # compiled ahead of time with DAGOR_DAS_AOT

set(sources)
set(deps daNetGame daNetGameLibs/dm/stub)
if(NOT DAGOR_DEDICATED AND DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources platform/windows/dng_empty.rc platform/windows/dng_empty.exe.manifest)
elseif(NOT DAGOR_DEDICATED AND NOT DAGOR_DAS_AOT_COMPILER AND NOT DAGOR_PLATFORM STREQUAL "linux")
  message(FATAL_ERROR "dng_empty: the ${DAGOR_PLATFORM} client's packaging is not ported yet")
endif()

dagor_add_dng_game(dng_empty GAME dng_empty
  # the linux dedicated server checks the clients' auth keys (NetPeerAuth): zero keys let any linux client in, set
  # real ones before shipping; windows and macOS clients are not checked
  AUTH_KEY_LINUX 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
  DEDICATED_AUTH linux linux
  CPP_DIRS main
  DNG_LIBS danetgamelibs.txt
  GAME_LIBS gamelibs.txt
  SOURCES ${sources}
  DAS_AOT ${das}
  AOT_SOURCES main/dasGameModulesList.cpp # the game's daScript modules, for its AOT compiler
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/daNetGameLibs ${DAGOR_PROG_DIR}/gameLibs
  DEPS ${deps}
  OUTPUT_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../game/${DAGOR_PLATFORM}-${DAGOR_ARCH}
)
