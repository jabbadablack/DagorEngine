# SPIRV-Cross, the SPIR-V to Metal Shading Language translator of the Metal shader compiler
set(sources
  spirv_cfg.cpp
  spirv_cross.cpp
  spirv_cross_parsed_ir.cpp
  spirv_parser.cpp
  spirv_cpp.cpp
  spirv_glsl.cpp
  spirv_msl.cpp
)
if(DAGOR_PLATFORM STREQUAL "macOS")
  set(options
    -Wno-deprecated-declarations
    -Wno-overriding-t-option
    -fno-fast-math
    -Wno-deprecated-this-capture
  )
endif()

dagor_add_library(SOURCES ${sources} COMPILE_OPTIONS ${options})
