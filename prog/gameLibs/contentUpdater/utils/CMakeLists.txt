# the updater's version numbers have one digit after the dot
set(gen "${CMAKE_CURRENT_BINARY_DIR}/gen")
file(CONFIGURE OUTPUT "${gen}/minorVersionDigitsCount.cpp"
  CONTENT "int get_updater_minor_version_digits_count() { return 1; }\n")

dagor_add_library(STRICT QUIRREL
  SOURCES pathUtils.cpp version.cpp "${gen}/minorVersionDigitsCount.cpp"
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
