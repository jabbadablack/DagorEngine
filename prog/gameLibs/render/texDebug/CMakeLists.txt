# Texture debug viewer (a stub in Rel)
dagor_add_library(STRICT
  SOURCES "$<IF:$<CONFIG:Rel>,${CMAKE_CURRENT_SOURCE_DIR}/texDebug_stub.cpp,${CMAKE_CURRENT_SOURCE_DIR}/texDebug.cpp>"
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude
)
