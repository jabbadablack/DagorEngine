# jsoncpp on EASTL containers (the engine's variant of 3rdPartyLibs/jsoncpp, whose license it carries)
set(includes ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include)
set(sources src/json_value.cpp src/json_reader.cpp src/json_writer.cpp)
list(APPEND deps 3rdPartyLibs/eastl)
list(APPEND license_files ${DAGOR_PROG_DIR}/3rdPartyLibs/jsoncpp)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps} LICENSE_FILES ${license_files})
