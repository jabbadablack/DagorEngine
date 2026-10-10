# daFrameGraph unit tests: the tests in tests/ and those embedded in the library's sources (flavor ut), with mock
# shader variables. They run on the stub driver (cases that need a GPU skip themselves); in trees with a real 3d
# driver also on that one (gameLibs.daFrameGraph, requires a GPU).
set(options)
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  set(options -Wc++11-narrowing -Wswitch -Wbitfield-constant-conversion -Wmissing-field-initializers)
endif()
dagor_add_catch2_test(daFrameGraph-tests STRICT
  TAGS gameLibs render
  TIMEOUT 1200
  ARGS --gpu-driver stub
  SOURCES
    main.cpp
    benchmark.cpp
    packer.cpp
    performance.cpp
    runtime.cpp
    multiplexing.cpp
    idContainers.cpp
    barrierScheduler.cpp
    cycAlloc.cpp
    bitSearch.cpp
    irGraphBuilder.cpp
    nodeStateDeltas.cpp
    nodeRemap.cpp
    resourceScheduler.cpp
    virtualPassRequest.cpp
    refinedBlock.cpp
  PRIVATE_INCLUDES .. ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  COMPILE_OPTIONS ${options}
  DEPS
    engine/memory
    engine/kernel
    engine/osApiWrappers
    engine/coreUtil
    engine/baseUtil
    engine/ioSys
    engine/math
    engine/shaders
    engine/lib3d
    engine/image
    engine/startup
    engine/workCycle
    engine/perfMon/stub
    engine/drv/drv3d_pc_multi
    engine/osApiWrappers/messageBox
    3rdPartyLibs/eastl
    gameLibs/render/daFrameGraph:ut
  PROPERTIES DAGOR_SHADER_VARS mock DAGOR_LINUX_GUI ON
)
set(real_drivers ${DAGOR_D3D_DRIVERS})
list(REMOVE_ITEM real_drivers stub null)
if(real_drivers)
  dagor_add_catch2_run(daFrameGraph-tests gameLibs.daFrameGraph TAGS gameLibs render REQUIRES gpu TIMEOUT 1200)
endif()
