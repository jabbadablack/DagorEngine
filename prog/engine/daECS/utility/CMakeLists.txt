# daECS utilities: entity helpers, templates DB, events
set(includes ${DAGOR_PROG_DIR}/3rdPartyLibs/eastl/include)
set(sources createInstantiated.cpp instantiateDependencies.cpp enumDescription.cpp)
list(APPEND deps engine/daECS/core)

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
