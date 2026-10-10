# Breakpad's common Windows code (string and GUID utilities) for its client
dagor_add_library(
  SOURCES string_utils.cc guid_string.cc
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/3rdPartyLibs/breakpad
  LICENSE_FILES ${DAGOR_PROG_DIR}/3rdPartyLibs/breakpad
)
