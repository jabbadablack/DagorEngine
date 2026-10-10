# dsc2-nodeBased: compiles the node-based shaders of the web UI's shader editors (the compiler flavor of
# gameLibs/webui/plugins/shaderEditors) into the dumps games load
set(deps
  engine/osApiWrappers
  engine/kernel
  engine/memory:default.off
  engine/ioSys
  engine/startup
  engine/baseUtil
  engine/math
  engine/perfMon/daProfilerStub
  gameLibs/webui/plugins/shaderEditors:comp
  tools/libTools/util
  3rdPartyLibs/regExp
)
if(DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND deps engine/osApiWrappers/messageBox/stub)
endif()

dagor_add_executable(dsc2-nodeBased CONSOLE CDK
  SOURCES main.cpp winmain_con.cpp
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/tools/sharedInclude
  DEPS ${deps}
)
