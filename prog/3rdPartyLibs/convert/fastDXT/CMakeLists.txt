# Fast DXT (BC1-3) compressors
set(sources fastDXT.cpp rygDXT.cpp)
if(DAGOR_ARCH MATCHES "^(e2k|x86_64)$")
  list(APPEND defines DXT_INTR)
endif()
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/convert/fastDXT)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} PRIVATE_DEFINES ${defines})
