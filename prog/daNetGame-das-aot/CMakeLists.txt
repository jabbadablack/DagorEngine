# The daScript AOT compiler of daNetGame's games (DagorDas.cmake): daScript with the C++ bindings of the framework's
# modules, which a game's compiler (dagor_add_dng_game in a DAGOR_DAS_AOT_COMPILER tree) links with its own. An object
# library: its modules register themselves, nothing references them.
if(NOT DAGOR_DAS_AOT_COMPILER)
  message(FATAL_ERROR "prog/daNetGame-das-aot is built in the trees of the AOT compilers (DAGOR_DAS_AOT_COMPILER)")
endif()

set(P ${DAGOR_PROG_DIR})
set(sources
  ${P}/daNetGame-das-aot/main.cpp
  ${P}/daNetGame-das-aot/da.cpp

  ${P}/1stPartyLibs/daScript/dagorAdapter/da_dummy.cpp
  ${P}/daNetGame/dasModules/actor.cpp
  ${P}/daNetGame/dasModules/app.cpp
  ${P}/daNetGame/dasModules/testMode.cpp
  ${P}/gameLibs/dasModules/auth/auth.cpp
  ${P}/gameLibs/dasModules/appTime/appTime.cpp
  ${P}/daNetGame/dasModules/camera.cpp
  ${P}/daNetGame/dasModules/cameraShaker.cpp
  ${P}/daNetGame/dasModules/capsuleApproximation.cpp
  ${P}/daNetGame/dasModules/collisionTraces.cpp
  ${P}/daNetGame/dasModules/dagorDebug3dSolid.cpp
  ${P}/daNetGame/dasModules/dgNet.cpp
  ${P}/daNetGame/dasModules/dngHostedServer.cpp
  ${P}/daNetGame/dasModules/gameObject.cpp
  ${P}/daNetGame/dasModules/gridCollision.cpp
  ${P}/daNetGame/dasModules/level.cpp
  ${P}/daNetGame/dasModules/netPhys.cpp
  ${P}/daNetGame/dasModules/propsRegistry.cpp
  ${P}/daNetGame/dasModules/netPropsRegistry.cpp
  ${P}/daNetGame/dasModules/netstat.cpp
  ${P}/daNetGame/dasModules/phys.cpp
  ${P}/daNetGame/dasModules/player.cpp
  ${P}/daNetGame/dasModules/replay.cpp
  ${P}/daNetGame/dasModules/scene.cpp
  ${P}/daNetGame/dasModules/smokeOccluder.cpp
  ${P}/daNetGame/dasModules/sound/aotSoundProps.cpp
  ${P}/daNetGame/dasModules/sound_net/aotSoundNetProps.cpp
  ${P}/daNetGame/dasModules/streaming.cpp
  ${P}/daNetGame/dasModules/ui.cpp
  ${P}/daNetGame/dasModules/dacoll.cpp
  ${P}/daNetGame/dasModules/matchingTypes.cpp
  ${P}/daNetGame/input/dasModules/touchInput.cpp
  ${P}/daNetGame/render/dasModules/clipmapDecals.cpp
  ${P}/daNetGame/render/dasModules/daSkies.cpp
  ${P}/daNetGame/render/dasModules/fx.cpp
  ${P}/daNetGame/render/dasModules/priorityManagedShadervar.cpp
  ${P}/daNetGame/render/dasModules/dagorMaterials.cpp
  ${P}/daNetGame/render/dasModules/worldRenderer.cpp
  ${P}/daNetGame/render/dasModules/heightmapQueryManager.cpp
  ${P}/daNetGame/render/dasModules/portalRenderer.cpp
  ${P}/daNetGame/render/dasModules/bvh.cpp

  ${P}/daNetGame/main/dedicated/dasModules/dngMatching.cpp

  ${P}/daNetGame-das-aot/stub.cpp
  ${P}/gameLibs/daRg/dasBinding.cpp

  ${P}/1stPartyLibs/daScript/modules/dasStdDlg/src/dasStdDlg.cpp
  ${P}/1stPartyLibs/daScript/modules/dasStdDlg/src/dasStdDlgNotImplemented.cpp

  # the daScript bindings of libraries (their _aot.jam)
  ${P}/gameLibs/render/outline/dasModules/outline.cpp
  ${P}/gameLibs/rendInst/aot/stub.cpp
  ${P}/gameLibs/daEditorE/aot/stub.cpp
)
# those that include their library's private headers (from the library's dir)
foreach(group
    "gameLibs/render/daFrameGraph:api/das/frameGraphModule.cpp;api/das/enumerations.cpp;api/das/nodeDataAnnotation.cpp;api/das/structureAnnotations.cpp;api/das/blobBindings.cpp;api/das/stub_aot.cpp"
    "gameLibs/render/resourceSlot:das/resourceSlotCoreModule.cpp;das/stub_aot.cpp"
    "gameLibs/ecs/deferToAct:deferToActModule.cpp;stub_aot.cpp")
  string(REGEX MATCH "^[^:]+" lib "${group}")
  string(REGEX REPLACE "^[^:]+:" "" files "${group}")
  list(TRANSFORM files PREPEND "${P}/${lib}/")
  set_property(SOURCE ${files} APPEND PROPERTY INCLUDE_DIRECTORIES "${P}/${lib}")
  list(APPEND sources ${files})
endforeach()
if(DAGOR_PLATFORM MATCHES "^(windows|linux|macOS)$")
  list(APPEND sources ${P}/daNetGame/dasModules/websocket/webSocket.cpp
    ${P}/daNetGame/dasModules/websocket/webSocketServer.cpp)
endif()
set(stringify ${P}/daNetGame/dasModules/dgNet.das ${P}/daNetGame/dasModules/dagorDebug3dSolid.das
  ${P}/daNetGame/render/dasModules/daSkies.das ${P}/daNetGame/render/dasModules/fx.das)
if(DAGOR_PLATFORM MATCHES "^(windows|linux|macOS)$")
  list(APPEND stringify ${P}/daNetGame/dasModules/websocket/webSocket.das)
endif()

dagor_add_library(OBJECT
  SOURCES ${sources}
  PRIVATE_INCLUDES
    ${P}/daNetGame
    ${P}/daNetGameLibs
    ${P}/3rdPartyLibs/rapidjson/include
    ${P}/engine/dagorInclude
    ${P}/gameLibs/publicInclude
    ${P}/gameLibs
    ${P}/1stPartyLibs/daScript/include
    ${P}/gameLibs/publicInclude/quirrel
    ${P}/1stPartyLibs/quirrel/quirrel/include
    ${P}/1stPartyLibs/jsoncpp/include
    ${P}/1stPartyLibs/rapidJsonUtils/include
    ${P}/3rdPartyLibs/recastnavigation/Detour/Include
  PUBLIC_DEFINES DAS_AOT_COMPILER
  QUIRREL
  STRINGIFY ${stringify}
  PUBLIC_DEPS
    engine/osApiWrappers
    engine/kernel
    engine/perfMon
    engine/math
    engine/gameRes
    engine/memory:rtl
    engine/consoleProc
    engine/drv/drv3d_null
    engine/baseUtil
    engine/startup
    engine/coreUtil
    engine/sceneRay
    engine/scene
    engine/imgui/stub
    engine/animChar/stub
    3rdPartyLibs/eastl
    1stPartyLibs/rapidJsonUtils
    1stPartyLibs/daScript
    1stPartyLibs/daScript/utils/dasFormatter
    1stPartyLibs/daScriptModules/rapidjson
    1stPartyLibs/daScript/modules/dasImgui
    1stPartyLibs/daScript/modules/dasQuirrel
    gameLibs/ecs/game/generic
    gameLibs/ecs/game/zones
    gameLibs/ecs/net
    engine/daECS/core
    engine/daECS/gameResStub
    engine/daECS/io/datablock
    engine/daECS/utility
    gameLibs/ecs/scripts/das
    gameLibs/dasModules/common
    gameLibs/dasModules/quirrel
    gameLibs/dasModules/phys
    gameLibs/dasModules/projectiveDecals
    gameLibs/dasModules/ECSGlobalTags
    gameLibs/dasModules/currentCircuit
    gameLibs/dasModules/gameMath
    gameLibs/dasModules/generic
    gameLibs/dasModules/sound
    gameLibs/dasModules/sound/common
    gameLibs/soundSystem/stub
    gameLibs/ecs/sound/stub
    gameLibs/dasModules/shaders
    gameLibs/dasModules/rendInst
    gameLibs/dasModules/daInput
    gameLibs/dasModules/actions
    gameLibs/dasModules/daProfiler
    gameLibs/dasModules/camera
    gameLibs/dasModules/render
    gameLibs/dasModules/stdGui
    gameLibs/dasModules/stdGui/aotStub
    gameLibs/dasModules/imgui
    gameLibs/dasModules/videoPlayer
    gameLibs/dasModules/gpuReadbackQuery
    gameLibs/dasModules/landMesh
    gameLibs/dasModules/systemInfo
    gameLibs/dasModules/compressionUtils
    gameLibs/dasModules/localization
    gameLibs/daGame/timers
    engine/daECS/net
    gameLibs/grid
    gameLibs/jsonUtils
    gameLibs/ecs/scripts/sq
    gameLibs/quirrel/bindQuirrelEx
    gameLibs/quirrel/quirrel_json
    gameLibs/quirrel/sqCrossCall
    gameLibs/spacePartition/looseGrid
    gameLibs/streaming
    gameLibs/dasModules/forceFeedback
    gameLibs/dasModules/net
    gameLibs/dasModules/clientNet
    gameLibs/dasModules/statsd
    gameLibs/daEditorE
    gameLibs/dasModules/daEditor
    gameLibs/propsRegistry
    gameLibs/statsd
    gameLibs/compressionUtils
    gameLibs/landMesh/stub
    gameLibs/gamePhys/collision/stub
    gameLibs/gamePhys/phys/stub
    gameLibs/gamePhys/props/stub
    gameLibs/render/debug3dSolid/stub
    gameLibs/dasModules/perFrameStat
    Dagor::Phys
)
