# daNetGame: the framework of the games on it (the client or the dedicated server of a game tree, DAGOR_DEDICATED),
# which link it with their own code (dagor_add_dng_game). Its switches are the tree's (DagorGame.cmake); those that
# jam turned off in Rel are generator expressions here, so these lists have parts that only some configurations build.
if(NOT DAGOR_VARIANT STREQUAL "game")
  message(FATAL_ERROR "prog/daNetGame is built in game trees (DAGOR_VARIANT game), not in a ${DAGOR_VARIANT} tree")
endif()

set(sources)
set(es)
set(das)
set(deps)
set(pulls)
set(includes)
set(system_libs)

# _dng_glob(<var> <cond> <glob> <dir>...): the files of the dirs, built where <cond> holds (1, 0 or a generator
# expression)
function(_dng_glob var cond glob)
  if(cond STREQUAL "0")
    return()
  endif()
  set(found)
  dagor_glob_sources(found DIRS ${ARGN} GLOB ${glob}
    EXCLUDE "/main/(main|version)\\.cpp$" "_ps[45]\\.cpp$") # main.cpp and version.cpp are the game's (game.jam)
  if(NOT cond STREQUAL "1")
    list(TRANSFORM found REPLACE "^(.+)$" "$<${cond}:\\1>")
  endif()
  set(${var} ${${var}} ${found} PARENT_SCOPE)
endfunction()

# _dng_files(<var> <cond> <file>...): the files, built where <cond> holds
function(_dng_files var cond)
  if(cond STREQUAL "0")
    return()
  endif()
  set(files)
  foreach(file IN LISTS ARGN)
    if(cond STREQUAL "1")
      list(APPEND files "${file}")
    else()
      list(APPEND files "$<${cond}:${CMAKE_CURRENT_SOURCE_DIR}/${file}>")
    endif()
  endforeach()
  set(${var} ${${var}} ${files} PARENT_SCOPE)
endfunction()

# _dng_not(<out> <cond>): the negation of a condition
function(_dng_not out cond)
  if(cond STREQUAL "0")
    set(${out} 1 PARENT_SCOPE)
  elseif(cond STREQUAL "1")
    set(${out} 0 PARENT_SCOPE)
  else()
    set(${out} "$<NOT:${cond}>" PARENT_SCOPE)
  endif()
endfunction()

# _dng_deps(<cond> <ref>... [ELSE <ref>...]): the libraries linked where <cond> holds, and those linked elsewhere
function(_dng_deps cond)
  cmake_parse_arguments(PARSE_ARGV 1 arg "" "" "ELSE")
  set(result ${deps})
  if(cond STREQUAL "1")
    list(APPEND result ${arg_UNPARSED_ARGUMENTS})
  elseif(cond STREQUAL "0")
    list(APPEND result ${arg_ELSE})
  else()
    dagor_use(${arg_UNPARSED_ARGUMENTS} ${arg_ELSE})
    foreach(ref IN LISTS arg_UNPARSED_ARGUMENTS)
      dagor_ref_target("${ref}" name)
      list(APPEND result "$<${cond}:${name}>")
    endforeach()
    foreach(ref IN LISTS arg_ELSE)
      dagor_ref_target("${ref}" name)
      list(APPEND result "$<$<NOT:${cond}>:${name}>")
    endforeach()
  endif()
  set(deps ${result} PARENT_SCOPE)
endfunction()

set(dev "$<NOT:$<CONFIG:Rel>>")
set(desktop OFF)
if(DAGOR_PLATFORM MATCHES "^(windows|linux|macOS)$")
  set(desktop ON)
endif()
set(desktop_dev 0)
if(desktop)
  set(desktop_dev "${dev}")
endif()
set(renderer 0)
if(DAGOR_GAME_RENDERER)
  set(renderer 1)
endif()
set(imgui "${DAGOR_GAME_IMGUI}")
_dng_not(no_imgui "${imgui}")
set(editor "${DAGOR_GAME_EDITOR}")
_dng_not(no_editor "${editor}")
set(webui "${DAGOR_GAME_WEBUI}")
_dng_not(no_webui "${webui}")

# --- the framework's own code ----------------------------------------------------------------------------------------
_dng_glob(sources 1 *.cpp main main/dasModulesList net game phys dasModules)
_dng_glob(es 1 *ES.cpp.inl main game net phys)
_dng_glob(das 1 *.das scripts/das/debug)
# the ImGui windows, outside Rel
_dng_glob(das "${imgui}" *.das scripts/das/imgui)
_dng_glob(sources "${imgui}" *.cpp ui/imgui)
_dng_glob(sources "${no_imgui}" *.cpp ui/imgui/stub)
_dng_glob(sources "${desktop_dev}" *.cpp dasModules/websocket)
# daScript modules embedded as text
set(stringify dasModules/dgNet.das dasModules/dagorDebug3dSolid.das render/dasModules/daSkies.das
  render/dasModules/fx.das)
if(desktop)
  list(APPEND stringify dasModules/websocket/webSocket.das)
endif()

if(DAGOR_DEDICATED)
  list(APPEND sources camera/stub/camstub.cpp)
  _dng_glob(sources 1 *.cpp net/dedicated main/dedicated main/dedicated/dasModules)
  _dng_glob(es 1 *ES.cpp.inl main/dedicated net/dedicated)
else()
  _dng_glob(sources 1 *.cpp net/dedicated/stub camera main/client main/client/dasModules)
  _dng_glob(es 1 *ES.cpp.inl camera main/client)
endif()

if(DAGOR_GAME_RENDERER)
  _dng_glob(es 1 *ES.cpp.inl render/fx render/animchar render/weather render/world render/world/frameGraphNodes
    render/grass render)
  _dng_glob(sources 1 *.cpp render/dasModules render/world render/world/frameGraphNodes
    render/world/frameGraphNodesMobile render/weather render)
else()
  list(APPEND sources render/stub/rendererStub.cpp render/stub/screencapStub.cpp render/stub/billboardStub.cpp
    render/stub/wind.cpp render/stub/cinematicModeStub.cpp)
endif()
if(DAGOR_GAME_FX)
  _dng_glob(sources 1 *.cpp render/fx)
else()
  list(APPEND sources render/stub/fxStub.cpp)
endif()
# the embedded daEditorE, outside Rel
_dng_files(sources "${editor}" editor/embeddedEditor.cpp editor/de4entityEditor.cpp editor/de4entityObj.cpp
  editor/de4sceneObj.cpp editor/editorDasModules.cpp)
_dng_glob(es "${editor}" *ES.cpp.inl editor)
_dng_files(sources "${no_editor}" editor/embeddedEditorStub.cpp)

if(DAGOR_GAME_DNG_INPUT)
  _dng_glob(sources 1 *.cpp input input/humanInput input/dasModules)
  _dng_glob(es 1 *ES.cpp.inl input input/humanInput)
else()
  list(APPEND sources input/stub/inputstub.cpp)
endif()
if(DAGOR_GAME_OVERLAY_UI)
  _dng_glob(es 1 *ES.cpp.inl ui ui/hud ui/bhv)
  _dng_glob(sources 1 *.cpp ui ui/hud ui/bhv ui/robj)
else()
  list(APPEND sources ui/stub/uiStub.cpp ui/stub/overlayUiStub.cpp)
endif()

# the memory manager: the debug allocator outside Rel on Windows, the system's on the Linux servers and with sanitizers
set(memory_leaks 0)
if(NOT DAGOR_SANITIZE STREQUAL "none")
  set(memory engine/memory:default.off)
elseif(DAGOR_PLATFORM STREQUAL "windows")
  set(memory "$<IF:$<CONFIG:Rel>,engine.memory.rtl,engine.memory.default.dbg>")
  dagor_use(engine/memory:rtl engine/memory:default.dbg)
  set(memory_leaks "${dev}")
elseif(DAGOR_PLATFORM STREQUAL "linux" AND DAGOR_DEDICATED)
  set(memory engine/memory:default.off)
else()
  set(memory engine/memory)
endif()
_dng_not(no_memory_leaks "${memory_leaks}")
_dng_files(sources "${memory_leaks}" main/opt/memleakDetector.cpp)
_dng_files(sources "${no_memory_leaks}" main/opt/memleakDetectorStub.cpp)

if(DAGOR_PLATFORM MATCHES "^(windows|linux)$" AND NOT DAGOR_DEDICATED)
  list(APPEND sources render/autoGraphics/autoGraphics.cpp)
else()
  list(APPEND sources render/stub/autoGraphicsStub.cpp) # a server renders nothing: no graphics preset to choose
endif()
_dng_files(sources "${webui}" main/webui/webui.cpp)
_dng_files(sources "${no_webui}" main/webui/stub.cpp)
list(APPEND sources main/browser/webBrowserStub.cpp) # no embedded browser (DAGOR_GAME_EMBEDDED_BROWSER)

# --- the libraries ---------------------------------------------------------------------------------------------------
if(NOT DAGOR_KERNEL_LINKAGE STREQUAL "dynamic")
  # the memory manager before the other libraries, for its static initializers to come early
  list(APPEND deps engine/osApiWrappers engine/kernel ${memory} engine/ioSys engine/baseUtil)
endif()
list(APPEND deps
  engine/startup
  engine/coreUtil
  engine/math
  engine/lib3d
  engine/image
  engine/unitTest
  engine/shaders
  engine/streaming
  engine/workCycle
  engine/guiBase
  engine/scene
  engine/phys/physCommon
  engine/sceneRay
  engine/animChar
  engine/anim
  engine/phys/fastPhys
  engine/ADT
  engine/crypto
  engine/gameRes
  engine/perfMon
  engine/profilerTracker

  gameLibs/daProfilerPlugins
  gameLibs/digitalSignature
  gameLibs/decalMatrices
  gameLibs/quirrel/sqDebugger
  gameLibs/quirrel/clientLog
  gameLibs/quirrel/sqJwt
  gameLibs/quirrel/yupfile_parse
  gameLibs/yup_parse
  gameLibs/fftWater
  gameLibs/heightmap
  engine/daNet
  gameLibs/daFracture/core
  gameLibs/daPhys
  gameLibs/physMap
  gameLibs/gamePhys/collision/collision-common
  gameLibs/gamePhys/collision/customRendinstTrace
  gameLibs/gamePhys/collision/rendinst
  gameLibs/gamePhys/props
  gameLibs/gamePhys/phys
  gameLibs/gamePhys/common
  gameLibs/sepClientInstance

  gameLibs/gameMath
  gameLibs/grid
  gameLibs/lagCatcher
  gameLibs/landMesh
  gameLibs/rendInst
  gameLibs/memoryProfiler
  gameLibs/camera
  gameLibs/camTrack
  gameLibs/folders
  gameLibs/webvromfs
  gameLibs/levelSplines
  gameLibs/dataBlockUtils
  gameLibs/dataBlockUtils/blk2sqrat
  gameLibs/jsonUtils
  gameLibs/video360
  gameLibs/streaming
  gameLibs/smokeOccluder
  gameLibs/hudprim
  gameLibs/perFrameStat

  engine/consoleProc
  engine/imgui

  gameLibs/daGame
  gameLibs/daGame/timers
  gameLibs/quirrel/bindQuirrelEx
  gameLibs/quirrel/sqCrossCall
  gameLibs/quirrel/quirrel_json
  gameLibs/quirrel/sqConsole
  gameLibs/quirrel/http
  gameLibs/quirrel/asyncRuntime
  gameLibs/quirrel/sqDacoll
  gameLibs/quirrel/sqStatsd
  gameLibs/quirrel/base64
  gameLibs/quirrel/sqDataCache
  gameLibs/quirrel/nestdb
  gameLibs/quirrel/sqSysInfo
  gameLibs/quirrel/lastInputMonitor
  gameLibs/quirrel/sqPerFrameStat

  gameLibs/ecs/scripts/das
  gameLibs/ecs/scripts/dasSq
  gameLibs/dasModules/common
  gameLibs/dasModules/appTime
  gameLibs/dasModules/quirrel
  gameLibs/dasModules/phys
  gameLibs/dasModules/generic
  gameLibs/dasModules/ECSGlobalTags
  gameLibs/dasModules/currentCircuit
  gameLibs/dasModules/gameMath
  gameLibs/dasModules/rendInst
  gameLibs/dasModules/daInput
  gameLibs/dasModules/actions
  gameLibs/dasModules/daProfiler
  gameLibs/dasModules/forceFeedback
  gameLibs/dasModules/net
  gameLibs/dasModules/statsd
  gameLibs/dasModules/gpuReadbackQuery
  gameLibs/dasModules/landMesh
  gameLibs/dasModules/systemInfo
  gameLibs/dasModules/compressionUtils
  gameLibs/dasModules/perFrameStat

  gameLibs/das/ecs
  gameLibs/das/math

  gameLibs/propsRegistry

  engine/daECS/core
  engine/daECS/net
  engine/daECS/net/timesync
  engine/daECS/net/replay
  engine/daECS/scene
  engine/daECS/utility
  gameLibs/ecs/phys
  gameLibs/ecs/anim
  gameLibs/ecs/gameres
  gameLibs/ecs/scripts/sq
  gameLibs/ecs/game/generic
  gameLibs/ecs/game/zones
  gameLibs/ecs/game/actions
  gameLibs/ecs/rendInst
  gameLibs/ecs/os
  gameLibs/ecs/deferToAct
  engine/daECS/hierarchyTransform
  gameLibs/ecs/net
  gameLibs/ecs/net/dasevents
  gameLibs/userSystemInfo
  gameLibs/statsd
  3rdPartyLibs/libb64

  gameLibs/ioEventsPoll
  gameLibs/eventLog

  gameLibs/publicConfigs
  gameLibs/syncVroms
  gameLibs/contentUpdater/binarycache
  gameLibs/contentUpdater/utils

  1stPartyLibs/sysinfo

  gameLibs/ecs/console

  1stPartyLibs/rapidJsonUtils
  1stPartyLibs/daScriptModules/rapidjson
  gameLibs/render/denoiser
  gameLibs/bvh
  gameLibs/render/rtsm
  gameLibs/render/rtr
  gameLibs/render/rtao
  gameLibs/render/ptgi
  gameLibs/render/quirrel
  gameLibs/render/objectMotionBlur
  gameLibs/render/indoorProbes

  gameLibs/gpuMemoryDumper
  gameLibs/resourcePool
  gameLibs/render/autoGraphics
  gameLibs/gpuMemoryInspector

  gameLibs/ecs/debug # the ECS debug tools (their pull: ecsDebug)
)
list(APPEND includes ${DAGOR_PROG_DIR}/gameLibs/render/animatedSplashScreen/public_api)
if(DAGOR_GAME_RENDERER)
  list(APPEND deps gameLibs/render/animatedSplashScreen gameLibs/render/cameraInCamera)
  list(APPEND pulls framework_cameraInCamera_pull)
else()
  list(APPEND deps gameLibs/render/animatedSplashScreen/stub)
endif()

if(DAGOR_GAME_DNG_INPUT)
  list(APPEND deps gameLibs/daInput gameLibs/ecs/input)
  _dng_deps("${imgui}" gameLibs/imguiInput ELSE gameLibs/imguiInput/stub)
else()
  list(APPEND deps gameLibs/imguiInput/stub gameLibs/daInput/stub)
endif()
if(DAGOR_GAME_OVERLAY_UI)
  list(APPEND deps gameLibs/quirrel/sqEventBus gameLibs/quirrel/ecsComputed)
endif()

if(DAGOR_PLATFORM MATCHES "^(windows|linux)$")
  list(APPEND deps gameLibs/webui/websocket)
else()
  list(APPEND deps gameLibs/webui/websocket/stub)
endif()
_dng_deps("${desktop_dev}" 3rdPartyLibs/mongoose)
set(shader_editors gameLibs/webui/plugins/shaderEditors/stub)
if(DAGOR_GAME_RENDERER AND DAGOR_PLATFORM STREQUAL "windows")
  set(shader_editors gameLibs/webui/plugins/shaderEditors)
endif()
_dng_deps("${webui}"
  gameLibs/webui
  gameLibs/webui/plugins/ecsviewer
  gameLibs/webui/plugins/editorCurves
  gameLibs/webui/plugins/colorpicker
  gameLibs/webui/plugins/webView
  gameLibs/webui/plugins/rendinstColors
  ${shader_editors}
  ELSE gameLibs/webui/stub gameLibs/webui/plugins/shaderEditors/stub)

if(DAGOR_GAME_FX)
  list(APPEND deps engine/libFx gameLibs/daFx gameLibs/effectManager)
endif()
_dng_deps("${editor}" gameLibs/daEditorE gameLibs/dasModules/daEditor)
list(APPEND deps gameLibs/daRg/browser/stub gameLibs/quirrel/sqWebBrowser/stub) # no embedded browser

if(DAGOR_GAME_RENDERER)
  list(APPEND deps
    3rdPartyLibs/image/avif
    3rdPartyLibs/image/jpeg-6b
    3rdPartyLibs/image/libpng-1.4.22
    3rdPartyLibs/image/psdRead
    3rdPartyLibs/image/tinyexr-1.0.8
    engine/screenShotSystem
    gameLibs/aviWriter
    engine/videoPlayer
    gameLibs/videoEncoder
    gameLibs/profileEventsGUI
    gameLibs/render
    gameLibs/render/occlusion
    gameLibs/collisionOccluders
    gameLibs/render/outline
    gameLibs/render/camouflage
    gameLibs/render/tracer
    gameLibs/render/cables
    gameLibs/render/genericLUT
    gameLibs/render/rainX7
    gameLibs/render/hdrRender
    gameLibs/render/heatHaze
    gameLibs/render/lruCollision
    gameLibs/render/wind
    gameLibs/render/waterRipples
    gameLibs/render/wakePs
    gameLibs/render/foam
    gameLibs/render/texDebug
    gameLibs/render/fastGrassBaker
    gameLibs/render/levelProfiler
    gameLibs/render/voxelizationTarget
    gameLibs/GIWindows
    gameLibs/daGI2
    gameLibs/voxelizedMedia
    gameLibs/ecs/render
    gameLibs/ecs/render/weather_effects
    gameLibs/ecs/camera
    gameLibs/ecs/weather
    gameLibs/ecs/lights
    gameLibs/daFracture/render
    gameLibs/rendInst/riFx
    gameLibs/projectiveDecals
    gameLibs/billboardDecals
    gameLibs/render/dof
    gameLibs/render/volumetricLights
    gameLibs/render/enviCover
    gameLibs/render/nodeBasedShader
    gameLibs/nodeBasedShaderManager
    gameLibs/fpsProfiler
    gameLibs/render/upscale
    gameLibs/textureUtil
    gameLibs/render/daFrameGraph # with its daScript and daECS integration in game trees (DAGOR_DAFG_FEATURES)
    gameLibs/render/metronome
    gameLibs/das/daFrameGraph
    gameLibs/render/resourceSlot
    gameLibs/render/shaderCacheWarmup
    gameLibs/render/antialiasing

    gameLibs/dasModules/shaders
    gameLibs/dasModules/render
    gameLibs/dasModules/stdGui
    gameLibs/dasModules/camera
    gameLibs/dasModules/projectiveDecals

    gameLibs/render/deviceResetTelemetry
    gameLibs/render/psoCacheLoader

    gameLibs/daSkies2
    gameLibs/daSkies2/debug
    gameLibs/iblCube
  )
  list(APPEND pulls daSkies2_clouds_field_debug_pull iblCube_ecs_pull_ref)
else()
  list(APPEND deps
    gameLibs/gamePhys/phys/destrRenderStub
    gameLibs/daFracture/renderStub
    gameLibs/render/cables/stub
    gameLibs/rendInst/riFx/stub
    gameLibs/render/hdrRender/stub
    gameLibs/render/enviCover/stub
    gameLibs/render/volumetricLights/stub
    gameLibs/render/nodeBasedShader/stub
    gameLibs/render/antialiasing/stub
  )
endif()
if(DAGOR_DAS_AOT)
  list(APPEND pulls daslib_DAS_pull_AOT)
endif()
_dng_deps("${imgui}" 1stPartyLibs/daScript/modules/dasImgui gameLibs/dasModules/imgui gameLibs/consoleWindow
  ELSE gameLibs/consoleWindow/consoleWindowStub)
if(DAGOR_DAS_AOT AND NOT imgui STREQUAL "0")
  list(APPEND pulls "$<${imgui}:daslib_imgui_DAS_pull_AOT>") # daslib's imgui modules
endif()
list(APPEND deps engine/imgui/util 1stPartyLibs/daScript/modules/dasQuirrel gameLibs/vr)
set(std_dlg 0)
if(DAGOR_GAME_RENDERER AND DAGOR_PLATFORM STREQUAL "windows")
  set(std_dlg "${dev}")
  if(DAGOR_GAME_ASSET_MANAGER)
    set(std_dlg 1)
  endif()
endif()
_dng_deps("${std_dlg}" 1stPartyLibs/daScript/modules/dasStdDlg ELSE 1stPartyLibs/daScript/modules/dasStdDlg/stub)
list(APPEND deps 3rdPartyLibs/openssl-3.x)

if(DAGOR_DEDICATED)
  # headless
  list(APPEND deps engine/drv/hid_nulldrv)
  if(DAGOR_PLATFORM STREQUAL "linux")
    list(APPEND deps engine/osApiWrappers/messageBox/stub engine/workCycle/stub)
  endif()
  list(APPEND deps
    gameLibs/quirrel/frp
    gameLibs/forceFeedback/stub
    gameLibs/consoleKeyBindings/consoleKeyBindingsStub
    gameLibs/daRg/stub
    engine/drv/drv3d_pc_multi # the stub (DAGOR_D3D_DRIVERS)
  )
else()
  list(APPEND deps
    engine/osApiWrappers/messageBox
    commonFx/commonFxGame
    gameLibs/daRg
    gameLibs/dasModules/clientNet
    gameLibs/dasModules/auth
    gameLibs/forceFeedback
    engine/drv/drv3d_pc_multi # the platform's drivers (DAGOR_D3D_DRIVERS)
  )
  _dng_deps("${DAGOR_GAME_CONSOLE}" gameLibs/visualConsole ELSE gameLibs/visualConsole/visconstub)
  set(key_bindings 0)
  if(DAGOR_PLATFORM MATCHES "^(windows|linux)$")
    set(key_bindings "$<AND:${DAGOR_GAME_CONSOLE},${dev}>")
  endif()
  _dng_deps("${key_bindings}" gameLibs/consoleKeyBindings ELSE gameLibs/consoleKeyBindings/consoleKeyBindingsStub)
  if(DAGOR_PLATFORM STREQUAL "windows")
    set(system_libs Ws2_32 shlwapi)
  elseif(DAGOR_PLATFORM STREQUAL "macOS")
    list(APPEND sources main/apple_main.mm)
  elseif(NOT DAGOR_PLATFORM STREQUAL "linux")
    message(FATAL_ERROR "daNetGame: the ${DAGOR_PLATFORM} client is not ported yet")
  endif()
  # keyboard, mouse and game controllers
  list(APPEND deps engine/drv/hid_keyboard engine/drv/hid_mouse)
  if(DAGOR_PLATFORM STREQUAL "windows")
    list(APPEND deps engine/drv/hid_joystick engine/drv/hid_gamepad_xinput engine/drv/hid_dinput)
  elseif(DAGOR_PLATFORM STREQUAL "macOS")
    list(APPEND deps engine/drv/hid_joystick_osx)
  else()
    list(APPEND deps engine/drv/hid_joystick_linux)
  endif()
endif()
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64" AND NOT DAGOR_DEDICATED)
  list(APPEND deps gameLibs/nvCacheTracker)
else()
  list(APPEND deps gameLibs/nvCacheTracker/stub)
endif()

# sound: FMOD Studio's (DAGOR_GAME_SOUND), and the sound events of the network (DAGOR_GAME_SOUND_NET)
if(DAGOR_GAME_SOUND)
  message(FATAL_ERROR "daNetGame: DAGOR_GAME_SOUND (FMOD Studio, DAGOR_SDK_FMOD_DIR) is not ported yet")
endif()
list(APPEND deps gameLibs/soundSystem/stub gameLibs/soundSystem/quirrel/stub gameLibs/ecs/sound/stub)
_dng_glob(sources 1 *.cpp sound/stub)
if(DAGOR_GAME_SOUND_NET)
  list(APPEND deps gameLibs/dasModules/sound/common)
  _dng_glob(sources 1 *.cpp sound_net sound/common sound/server dasModules/sound/common dasModules/sound_net)
  _dng_glob(es 1 *ES.cpp.inl sound_net sound/common sound/server dasModules/sound/common)
else()
  _dng_glob(sources 1 *.cpp sound_net/stub)
endif()
if(DAGOR_BREAKPAD)
  list(APPEND deps gameLibs/breakpad/binder)
else()
  list(APPEND deps gameLibs/breakpad/stub)
endif()

# --- generated code --------------------------------------------------------------------------------------------------
set(gen "${CMAKE_CURRENT_BINARY_DIR}/gen")
if(DAGOR_GAME_RENDERER)
  file(CONFIGURE OUTPUT "${gen}/iblCubePullRef.cpp" CONTENT
    "#include <stddef.h>\nextern const size_t ecs_pull_iblCube;\nsize_t iblCube_ecs_pull_ref = (size_t)(&ecs_pull_iblCube);\n")
  list(APPEND sources "${gen}/iblCubePullRef.cpp")
else()
  # daSkies' clouds rain map pull, which a renderless build has not
  file(CONFIGURE OUTPUT "${gen}/daSkies2PullStub.cpp" CONTENT
    "#include <stddef.h>\nextern const size_t ecs_pull_cloudsRainMap = (size_t)(&ecs_pull_cloudsRainMap);\n")
  list(APPEND sources "${gen}/daSkies2PullStub.cpp")
endif()
# the pull of the framework's entity systems
set(es_pulls)
foreach(file IN LISTS es)
  _dagor_config_source("${file}" cond path)
  if(path)
    set(file "${path}")
  endif()
  cmake_path(GET file FILENAME name)
  string(REGEX REPLACE "ES\\.cpp\\.inl$" "" name "${name}")
  if(cond)
    list(APPEND es_pulls "$<${cond}:${name}>")
  else()
    list(APPEND es_pulls "${name}")
  endif()
endforeach()
_dagor_pull_file(sources "${gen}/daNetGame_es_pull.cpp" ECS framework_es_pulls ${es_pulls} ecsDebug)
# the daScript pulls of the client and the server: the tree's with DAGOR_DAS_AOT (DAS_AOT_PULL), 0 otherwise
set(das_pull daNetGame_client_DAS_pull_AOT)
if(DAGOR_DEDICATED)
  set(das_pull daNetGame_server_DAS_pull_AOT)
endif()
set(text "#include <stddef.h>\n")
if(NOT DAGOR_DAS_AOT OR DAGOR_DEDICATED)
  string(APPEND text "size_t daNetGame_client_DAS_pull_AOT = 0;\n")
endif()
if(NOT DAGOR_DAS_AOT OR NOT DAGOR_DEDICATED)
  string(APPEND text "size_t daNetGame_server_DAS_pull_AOT = 0;\n")
endif()
if(DAGOR_DAS_AOT)
  string(APPEND text "bool NEED_DAS_AOT_COMPILE = true;\n")
else()
  string(APPEND text "bool NEED_DAS_AOT_COMPILE = false;\n")
endif()
file(CONFIGURE OUTPUT "${gen}/dasAot.cpp" CONTENT "${text}")
list(APPEND sources "${gen}/dasAot.cpp")

# --- the library -----------------------------------------------------------------------------------------------------
list(REMOVE_DUPLICATES sources)
list(REMOVE_DUPLICATES es)
set(source_options)
if(DAGOR_DEDICATED AND DAGOR_PLATFORM STREQUAL "linux")
  list(APPEND source_options net/dedicated/netded.cpp -DNET_PEER_AUTH) # the clients' auth keys (NetPeerAuth)
endif()
dagor_add_library(STRICT QUIRREL
  SOURCES ${sources}
  ES_SOURCES ${es}
  DAS_AOT ${das}
  DAS_AOT_PULL ${das_pull}
  PCH precompile.h # (jam used it in Dev and Dbg only)
  PRIVATE_INCLUDES
    ${DAGOR_DNG_INCLUDES}
    ${DAGOR_PROG_DIR}/3rdPartyLibs/openssl-3.x/include
    ${DAGOR_PROG_DIR}/engine/sharedInclude
    ${DAGOR_PROG_DIR}/engine
    ${includes}
  PRIVATE_DEFINES DISABLE_SYNC_DEBUG # the fork has no gameLibs/syncDebug
  COMPILE_OPTIONS ${DAGOR_DNG_OPTIONS}
  SOURCE_OPTIONS ${source_options}
  DEPS ${deps} Dagor::Phys
  SYSTEM_LIBS ${system_libs}
  STRINGIFY ${stringify}
)
if(source_options)
  # its own definition: not with the precompiled header
  set_source_files_properties(net/dedicated/netded.cpp PROPERTIES SKIP_PRECOMPILE_HEADERS ON)
endif()
dagor_game_lib(PULLS ${pulls})
