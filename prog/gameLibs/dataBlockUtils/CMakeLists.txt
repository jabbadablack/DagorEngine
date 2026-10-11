# Ported from prog/gameLibs/dataBlockUtils/jamfile (jam2cmake/skeleton.py)
set(includes
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${CMAKE_CURRENT_SOURCE_DIR}
)
set(sources interpolateBlk.cpp blk2json.cpp blkUtils.cpp blkIterator.cpp)
list(APPEND deps 1stPartyLibs/jsoncpp)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
