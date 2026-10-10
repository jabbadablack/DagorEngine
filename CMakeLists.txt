# The engine's own build: its unit tests (DAGOR_VARIANT=tests), tools (cdk, editor, maxplug), dargbox, or all of it.
# Games and samples are separate projects with their own top-level CMakeLists.txt (see templates/dng-empty).
# Configure with a preset: cmake --preset windows-tests (cmake --list-presets shows them).
cmake_minimum_required(VERSION 4.0)
include(prog/cmake/DagorBootstrap.cmake)
project(DagorEngine LANGUAGES C CXX)
include(DagorEngine)

if(DAGOR_VARIANT MATCHES "^(tests|all)$")
  dagor_use_tests()
endif()
# the CDK: the command-line tools of the content pipeline (shader compilers, packers, converters), on the static kernel
if(DAGOR_VARIANT MATCHES "^(cdk|all)$")
  dagor_use(
    3rdPartyLibs/legacy_parser/dolphin
    3rdPartyLibs/legacy_parser/whale
    3rdPartyLibs/scripts/duktape
    tools/consoleSq
    tools/converters/ddsConverter
    tools/converters/ddsx2dds
    tools/converters/ddsxCvt
    tools/converters/GuiTex
    tools/FontGenerator
    tools/sceneTools/assetExp/ddsxConv
    tools/sceneTools/csvUtil
    tools/sceneTools/dbldUtil
    tools/sceneTools/dumpGrp
    tools/sceneTools/resClean
    tools/sceneTools/resDiff
    tools/sceneTools/resUpdate
    tools/sceneTools/utils
    tools/sceneTools/vromfsPacker
    tools/shaderInfo
    tools/ShaderCompiler2
    tools/ShaderCompiler2/nodeBased
    tools/sceneTools/guiShaders_commonData
  )
  # the data the tools load that is not built (prog/tools/toolsData/README.md), with the cdk-data component
  install(DIRECTORY prog/tools/toolsData/ DESTINATION tools COMPONENT cdk-data PATTERN README.md EXCLUDE)
endif()
# the tools on the shared kernel (daKernel): daBuild with its exporter plugins, ddsxCvt2
if(DAGOR_VARIANT MATCHES "^(editor|all)$")
  dagor_use(
    tools/libTools/daKernel
    tools/sceneTools/assetExp
    tools/sceneTools/assetExp/exporters
    tools/sceneTools/assetExp/refProviders
    gameLibs/vehiclePhys/exporters
    tools/converters/ddsxCvt2
  )
endif()

dagor_finalize()
