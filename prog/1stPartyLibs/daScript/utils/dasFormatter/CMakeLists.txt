# The daScript source formatter (das-fmt) as a library
set(sources ds_parser.cpp fmt.cpp formatter.cpp helpers.cpp)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
