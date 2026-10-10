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
    tools/sceneTools/csvUtil
    tools/sceneTools/dbldUtil
    tools/sceneTools/dumpGrp
    tools/sceneTools/resClean
    tools/sceneTools/resDiff
    tools/sceneTools/resUpdate
    tools/sceneTools/vromfsPacker
    tools/shaderInfo
    tools/ShaderCompiler2
    tools/ShaderCompiler2/nodeBased
  )
endif()

dagor_finalize()
