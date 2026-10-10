# Digital signature creation and checking on OpenSSL
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
list(APPEND includes ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include)
set(sources digitalSignatureCheck.cpp digitalSignatureCreate.cpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes})
