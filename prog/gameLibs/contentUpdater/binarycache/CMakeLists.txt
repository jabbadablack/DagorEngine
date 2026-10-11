# Ported from prog/gameLibs/contentUpdater/binarycache/jamfile (jam2cmake/skeleton.py)
set(sources binaryCache.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)

dagor_add_library(STRICT QUIRREL SOURCES ${sources} PRIVATE_INCLUDES ${includes})
