# Unit test support of <unittest/dag_testEnv.h>: test environment, reference images
set(sources testEnv.cpp imageReference.cpp)
set(deps engine/image)

dagor_add_library(STRICT SOURCES ${sources} DEPS ${deps})
