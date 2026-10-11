# daScript's standard dialogs module where there are none: the sources are in the parent dir
dagor_add_library(STRICT
  SOURCES ../src/dasStdDlg.cpp ../src/dasStdDlgNotImplemented.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  DEPS 1stPartyLibs/daScript
)
