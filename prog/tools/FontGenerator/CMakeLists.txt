# fontgen2: builds the engine's bitmap/SDF font atlases from TrueType/OpenType fonts (FreeType, HarfBuzz)
set(sources winmain_con.cpp fontGenerator.cpp fontfilesave.cpp freeTypeFont.cpp)
set(includes
  ${DAGOR_PROG_DIR}/3rdPartyLibs/freetype/freetype-2.8/include
  ${DAGOR_PROG_DIR}/tools/sharedInclude
  ${DAGOR_PROG_DIR}/engine/sharedInclude
)
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/image
  engine/perfMon/daProfilerStub
  tools/libTools/dtx
  tools/libTools/util
  3rdPartyLibs/freetype/freetype-2.8
  3rdPartyLibs/image/psdRead
  3rdPartyLibs/image/libpng-1.4.22
  3rdPartyLibs/image/avif
  3rdPartyLibs/image/jpeg-6b
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(fontgen2 CONSOLE CDK SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
