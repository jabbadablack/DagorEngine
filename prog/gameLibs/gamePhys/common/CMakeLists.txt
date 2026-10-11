# Ported from prog/gameLibs/gamePhys/common/jamfile (jam2cmake/skeleton.py)
set(includes ${DAGOR_PROG_DIR}/gameLibs/publicInclude)
set(sources
  loc.cpp
  polares.cpp
  mass.cpp
  kinematics.cpp
  fixed_dt.cpp
  chainIKSolver.cpp
  constraintChainIKSolver.cpp
)
if(DAGOR_CC MATCHES "^(clang|clang\-cl)$" AND DAGOR_PLATFORM STREQUAL "linux" AND DAGOR_ARCH STREQUAL "x86_64")
  list(APPEND source_options chainIKSolver.cpp -mno-avx2)
endif()

dagor_add_library(STRICT SOURCES ${sources} PRIVATE_INCLUDES ${includes} SOURCE_OPTIONS ${source_options})
