# Data cache: the file backend
set(includes ${DAGOR_PROG_DIR}/engine/dagorInclude ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(deps 3rdPartyLibs/eastl gameLibs/datacache/common)
set(sources filebackend.cpp fileentry.cpp fileutil.cpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
