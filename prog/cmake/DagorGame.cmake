# Games on daNetGame (DAGOR_VARIANT game: the trees of projects, e.g. templates/dng-empty): the game's switches, its
# modules (daNetGameLibs, gameLibs built like them) and the game program.
include_guard(GLOBAL)

# --- the game's switches (prog/daNetGame/setup.jam) -------------------------------------------------------------------
# DAGOR_GAME_<X> is ON or OFF for the whole tree. Those jam left out of Rel builds only are generator expressions that
# are true in the other configurations, for $<IF:...> and $<...:...> (DAGOR_GAME_DEV: not Rel):
#   DAGOR_GAME_EDITOR (embedded daEditorE), DAGOR_GAME_WEBUI, DAGOR_GAME_CONSOLE, DAGOR_GAME_IMGUI
set(DAGOR_GAME_DEV "$<NOT:$<CONFIG:Rel>>")
if(DAGOR_DEDICATED)
  set(DAGOR_GAME_RENDERER OFF) # headless
else()
  set(DAGOR_GAME_RENDERER ON)
endif()
set(DAGOR_GAME_FX ${DAGOR_GAME_RENDERER})
set(DAGOR_GAME_OVERLAY_UI ${DAGOR_GAME_RENDERER})
set(DAGOR_GAME_DNG_INPUT ${DAGOR_GAME_RENDERER})
set(DAGOR_GAME_CONTENT_UPDATER ${DAGOR_GAME_RENDERER})
set(DAGOR_GAME_SOUND_NET ON)
# sound needs FMOD, which is not redistributable (DAGOR_SDK_FMOD_DIR)
option(DAGOR_GAME_SOUND "The game client's sound (FMOD Studio, DAGOR_SDK_FMOD_DIR)" OFF)
if(DAGOR_DEDICATED)
  set(DAGOR_GAME_SOUND OFF)
endif()
set(DAGOR_GAME_EMBEDDED_BROWSER OFF)
set(DAGOR_GAME_ASSET_MANAGER OFF)
# BVH ray tracing: on the platforms and CPUs that have it
set(DAGOR_GAME_BVH OFF)
if(DAGOR_GAME_RENDERER AND ((DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64" AND DAGOR_SSE EQUAL 4)
                            OR DAGOR_PLATFORM STREQUAL "linux"))
  set(DAGOR_GAME_BVH ON)
endif()
set(DAGOR_BVH_STUBS grass) # without the random grass (prog/gameLibs/bvh/CMakeLists.txt)
# the render graph with its daScript bindings and its daECS nodes (prog/gameLibs/render/daFrameGraph)
if(DAGOR_VARIANT STREQUAL "game")
  set(DAGOR_DAFG_FEATURES das ecs)
endif()
# the developer features outside Rel
if(DAGOR_GAME_RENDERER AND DAGOR_PLATFORM MATCHES "^(windows|linux|macOS)$")
  set(DAGOR_GAME_EDITOR "${DAGOR_GAME_DEV}")
else()
  set(DAGOR_GAME_EDITOR 0)
endif()
if(DAGOR_DEDICATED AND DAGOR_PLATFORM STREQUAL "linux")
  set(DAGOR_GAME_WEBUI 0)
else()
  set(DAGOR_GAME_WEBUI "${DAGOR_GAME_DEV}")
endif()
if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_ARCH STREQUAL "x86_64")
  set(DAGOR_GAME_CONSOLE 1)
else()
  set(DAGOR_GAME_CONSOLE "${DAGOR_GAME_DEV}")
endif()
if(DAGOR_GAME_RENDERER)
  set(DAGOR_GAME_IMGUI "${DAGOR_GAME_DEV}")
else()
  set(DAGOR_GAME_IMGUI 0)
endif()

# the include dirs of daNetGame and the game programs (prog/daNetGame/setup.jam)
set(DAGOR_DNG_INCLUDES
  ${DAGOR_PROG_DIR}/daNetGame
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude
  ${DAGOR_PROG_DIR}/gameLibs/publicInclude/quirrel
  ${DAGOR_PROG_DIR}/gameLibs/render/screenSpaceReflection
  ${DAGOR_PROG_DIR}/commonFx/commonFxGame
  ${DAGOR_PROG_DIR}/3rdPartyLibs/recastnavigation/Detour/Include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/recastnavigation/DetourTileCache/Include
  ${DAGOR_PROG_DIR}/1stPartyLibs/jsoncpp/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/rapidJsonUtils/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zlib-ng
  ${DAGOR_PROG_DIR}/3rdPartyLibs/arc/zstd-1.4.5 # xxhash
  ${DAGOR_PROG_DIR}/3rdPartyLibs/libb64/include
  ${DAGOR_PROG_DIR}/3rdPartyLibs/rapidjson/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include
  ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/modules/dasQuirrel/src
)
# and their options: clang's unused variables are errors there
set(DAGOR_DNG_OPTIONS)
if(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  set(DAGOR_DNG_OPTIONS -Werror=unused-variable)
endif()

# --- modules (prog/_jBuild/build_module.jam)--------------------------------------------------------------------------
# dagor_add_dng_module(<module> [CPP_DIRS <dir>...] [ES_DIRS <dir>...] [DAS [DAS_DIRS <dir>...]] [PULL_VARS <name>...]
#                      <dagor_add_library arguments>...)
# A game module in the calling directory (daNetGameLibs/<module>, or a gameLibs dir built like one): the .cpp of
# CPP_DIRS, the entity systems (*ES.cpp.inl) of ES_DIRS, and the pull file that references them all
# (framework_<module>_pull, with PULL_VARS). A DAS module has the pull <prefix>_<module>_DAS_pull_AOT of its daScript
# (*.das of DAS_DIRS, maybe none in a tree): compiled ahead of time with DAGOR_DAS_AOT, 0 without.
function(dagor_add_dng_module module)
  cmake_parse_arguments(PARSE_ARGV 1 arg "DAS" "" "CPP_DIRS;ES_DIRS;DAS_DIRS;PULL_VARS")
  _dagor_base_dir(base)
  _dagor_dir_ref("${base}" ref)
  dagor_ref_target("${ref}" name)
  string(REGEX MATCH "^[^/]+" prefix "${ref}")
  set(sources)
  if(arg_CPP_DIRS)
    dagor_glob_sources(sources DIRS ${arg_CPP_DIRS} GLOB *.cpp)
  endif()
  set(es)
  if(arg_ES_DIRS)
    dagor_glob_sources(es DIRS ${arg_ES_DIRS} GLOB *ES.cpp.inl)
  endif()

  # the pull of the module's entity systems
  set(gen_dir "${CMAKE_CURRENT_BINARY_DIR}/gen/${name}")
  set(pulls ${arg_PULL_VARS})
  foreach(file IN LISTS es)
    cmake_path(GET file FILENAME es_name)
    string(REGEX REPLACE "ES\\.cpp\\.inl$" "" es_name "${es_name}")
    list(APPEND pulls "${es_name}")
  endforeach()
  _dagor_pull_file(sources "${gen_dir}/${module}_es_pull.cpp" ECS "framework_${module}_pull" ${pulls})

  # the daScript of the module: compiled ahead of time with its pull, or the pull variable alone
  set(das)
  if(arg_DAS_DIRS)
    dagor_glob_sources(das DIRS ${arg_DAS_DIRS} GLOB *.das)
  endif()
  string(MAKE_C_IDENTIFIER "${prefix}-${module}_DAS_pull_AOT" das_pull)
  set(aot_pull)
  if(arg_DAS)
    set(aot_pull ${das_pull})
  endif()
  if(arg_DAS AND NOT DAGOR_DAS_AOT)
    file(CONFIGURE OUTPUT "${gen_dir}/${module}_das_aot_pull.cpp" CONTENT "#include <stddef.h>\nsize_t ${das_pull} = 0;\n")
    list(APPEND sources "${gen_dir}/${module}_das_aot_pull.cpp")
  endif()

  dagor_add_library(${name} STRICT QUIRREL
    SOURCES ${sources}
    ES_SOURCES ${es}
    DAS_AOT ${das}
    DAS_AOT_PULL ${aot_pull}
    PRIVATE_DEFINES DISABLE_SYNC_DEBUG # the fork has no gameLibs/syncDebug
    ${arg_UNPARSED_ARGUMENTS}
  )
endfunction()

# _dagor_pull_file(<sources-var> <file> ECS|EXTERN <variable> <pull>...): appends to <sources-var> the source that
# defines size_t <variable>, the sum of the pulls, which makes the linker keep the objects that define them:
# ECS_PULL_VAR(<pull>) of entity systems (jam's make_es_pull_cpp.py) or plain extern size_t variables
# (make_module_pull_cpp.py). A pull $<cond:name> is there in the configurations where cond holds (a source per
# configuration then, see _dagor_config_generate).
function(_dagor_pull_file sources_var file kind variable)
  set(bs "\\")
  set(text "#include <daECS/core/componentType.h>\n#define REG_SYS${bs}\n")
  set(per_config OFF)
  foreach(pull IN LISTS ARGN)
    if(pull MATCHES "^\\$<(.+):([A-Za-z_][A-Za-z0-9_]*)>$")
      string(APPEND text "$<${CMAKE_MATCH_1}:  RS(${CMAKE_MATCH_2})${bs}\n>")
      set(per_config ON)
    else()
      string(APPEND text "  RS(${pull})${bs}\n")
    endif()
  endforeach()
  if(kind STREQUAL "ECS")
    string(APPEND text "\n#define RS(x) ECS_DECL_PULL_VAR(x);\nREG_SYS\n#undef RS\n#define RS(x) + ECS_PULL_VAR(x)\n")
  else()
    string(APPEND text "\n#define RS(x) extern size_t x;\nREG_SYS\n#undef RS\n#define RS(x) + (x)\n")
  endif()
  string(APPEND text "size_t ${variable} = 0 REG_SYS;\n")
  set(sources ${${sources_var}})
  if(per_config)
    _dagor_config_generate(sources "${file}" "${text}")
  else()
    file(CONFIGURE OUTPUT "${file}" CONTENT "${text}")
    list(APPEND sources "${file}")
  endif()
  set(${sources_var} "${sources}" PARENT_SCOPE)
endfunction()

# _dagor_config_generate(<sources-var> <file> <content>): <content> with generator expressions, written per
# configuration (<file> with -<config> before its extension); appends the sources, each for its configuration
function(_dagor_config_generate sources_var file content)
  cmake_path(REMOVE_EXTENSION file LAST_ONLY OUTPUT_VARIABLE stem)
  cmake_path(GET file EXTENSION LAST_ONLY ext)
  file(GENERATE OUTPUT "${stem}-$<CONFIG>${ext}" CONTENT "${content}")
  set(configs ${CMAKE_CONFIGURATION_TYPES})
  if(NOT configs)
    set(configs "${CMAKE_BUILD_TYPE}")
  endif()
  set(sources ${${sources_var}})
  foreach(config IN LISTS configs)
    list(APPEND sources "$<$<CONFIG:${config}>:${stem}-${config}${ext}>")
  endforeach()
  set(${sources_var} "${sources}" PARENT_SCOPE)
endfunction()

# --- what a library adds to the game program (the libraries' _lib.jam) ---------------------------------------------
# dagor_game_lib([PULLS <pull>...] [INCLUDES <dir>...] [DEPS <ref>...] [SOURCES <file>...]): the game program of the
# tree (dagor_add_dng_game; its AOT compiler in a DAGOR_DAS_AOT_COMPILER tree) references the pulls, compiles with the
# include dirs and the sources, and links the libraries
function(dagor_game_lib)
  cmake_parse_arguments(PARSE_ARGV 0 arg "" "" "PULLS;INCLUDES;DEPS;SOURCES")
  get_property(game GLOBAL PROPERTY DAGOR_GAME_TARGET)
  if(NOT game)
    message(FATAL_ERROR "dagor_game_lib() in ${CMAKE_CURRENT_SOURCE_DIR}: the tree has no game (dagor_add_dng_game)")
  endif()
  set_property(TARGET ${game} APPEND PROPERTY DAGOR_GAME_PULLS ${arg_PULLS})
  _dagor_abs_paths(includes ${arg_INCLUDES})
  if(includes)
    target_include_directories(${game} PRIVATE ${includes})
  endif()
  _dagor_link(${game} PRIVATE ${arg_DEPS})
  _dagor_abs_paths(sources ${arg_SOURCES})
  if(sources)
    target_sources(${game} PRIVATE ${sources})
  endif()
endfunction()

# _dagor_dng_lib_files(<out-var> <file> <danetgamelibs.txt> <gamelibs.txt>): <file> (_lib.cmake, _aot.cmake) of each
# lib of the lists that has one: the dirs of prog/daNetGameLibs and prog/gameLibs they name, one per line (# comments).
# A lib without the file has only content (scripts, templates, shaders).
function(_dagor_dng_lib_files out file dng_libs game_libs)
  set(result)
  foreach(kind DNG GAME)
    if(kind STREQUAL "DNG")
      set(list_file "${dng_libs}")
      set(root daNetGameLibs)
    else()
      set(list_file "${game_libs}")
      set(root gameLibs)
    endif()
    if(NOT list_file)
      continue()
    endif()
    _dagor_abs_paths(list_file "${list_file}")
    set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${list_file}")
    file(STRINGS "${list_file}" lines)
    foreach(line IN LISTS lines)
      string(REGEX REPLACE "#.*" "" line "${line}")
      string(STRIP "${line}" line)
      if(NOT line)
        continue()
      endif()
      if(NOT IS_DIRECTORY "${DAGOR_PROG_DIR}/${root}/${line}")
        message(FATAL_ERROR "${list_file}: there is no prog/${root}/${line}")
      endif()
      if(EXISTS "${DAGOR_PROG_DIR}/${root}/${line}/${file}")
        list(APPEND result "${DAGOR_PROG_DIR}/${root}/${line}/${file}")
      endif()
    endforeach()
  endforeach()
  set(${out} "${result}" PARENT_SCOPE)
endfunction()

# --- the game program (prog/daNetGame/game.jam) -----------------------------------------------------------------------
# dagor_add_dng_game(<target> GAME <codename> [WINDOW_TITLE <title>] [USER_DIR <dir>] [MAIN_VROM <path>]
#   [AUTH_KEY_<PLATFORM> <20 bytes>] (PLATFORM: WINDOWS LINUX MACOS ANDROID IOS) [DEDICATED_AUTH <prefix> <platform>...]
#   [LOG_CRYPT_KEY <128 bytes>] [CPP_DIRS <dir>...] [ES_DIRS <dir>...] [PULLS <pull>...]
#   [DNG_LIBS <danetgamelibs.txt>] [GAME_LIBS <gamelibs.txt>] [AOT_SOURCES <file>...]
#   <dagor_add_executable arguments>...)
# The game: daNetGame's main, the .cpp of CPP_DIRS and the entity systems of ES_DIRS, the code game.jam generated
# (gameproj:: names and paths, auth keys, the pull of every module and library) and the libraries of the lists, whose
# CMakeLists add what they need to it (dagor_game_lib). The client is named <codename>, the dedicated server
# <codename>-ded. LOG_CRYPT_KEY encrypts the logs of Rel and IRel builds with DAGOR_FORCE_LOGS. In the tree of the
# game's daScript AOT compiler (DAGOR_DAS_AOT_COMPILER) it makes <codename>-aot instead, with the AOT_SOURCES.
function(dagor_add_dng_game target)
  set(key_args)
  foreach(platform WINDOWS LINUX MACOS ANDROID IOS)
    list(APPEND key_args AUTH_KEY_${platform})
  endforeach()
  cmake_parse_arguments(PARSE_ARGV 1 arg "${_DAGOR_TARGET_OPTIONS}"
    "GAME;WINDOW_TITLE;USER_DIR;MAIN_VROM;DNG_LIBS;GAME_LIBS;${_DAGOR_TARGET_ONE_VALUE}"
    "CPP_DIRS;ES_DIRS;PULLS;DEDICATED_AUTH;LOG_CRYPT_KEY;AOT_SOURCES;${key_args};${_DAGOR_TARGET_MULTI_VALUE}")
  if(arg_UNPARSED_ARGUMENTS)
    message(FATAL_ERROR "dagor_add_dng_game(${target}): unexpected arguments: ${arg_UNPARSED_ARGUMENTS}")
  endif()
  if(NOT arg_DAS_AOT_PULL)
    set(arg_DAS_AOT_PULL ${arg_GAME}_DAS_pull_AOT)
  endif()
  _dagor_forward_target_args(forward arg EXCLUDE SOURCES ES_SOURCES STRICT QUIRREL OUTPUT_NAME)
  if(NOT arg_GAME OR arg_GAME MATCHES "[A-Z]")
    message(FATAL_ERROR "dagor_add_dng_game(${target}): GAME <codename> in lowercase is required (it names the vromfs)")
  endif()
  set(game "${arg_GAME}")
  foreach(var WINDOW_TITLE USER_DIR)
    if(NOT arg_${var})
      set(arg_${var} "${game}")
    endif()
  endforeach()
  if(NOT arg_MAIN_VROM)
    set(arg_MAIN_VROM "${game}.vromfs.bin")
  endif()
  foreach(var IN LISTS key_args)
    list(LENGTH arg_${var} n)
    if(arg_${var} AND NOT n EQUAL 20)
      message(FATAL_ERROR "dagor_add_dng_game(${target}): ${var} must be 20 bytes, not ${n}")
    endif()
  endforeach()
  cmake_path(GET arg_MAIN_VROM PARENT_PATH vrom_dir)
  set_property(GLOBAL PROPERTY DAGOR_GAME_TARGET "${target}")
  set_property(GLOBAL PROPERTY DAGOR_GAME_CODENAME "${game}")
  set_property(GLOBAL PROPERTY DAGOR_DAS_AOT_DIR "${CMAKE_CURRENT_SOURCE_DIR}") # where the AOT compiler runs
  if(DAGOR_DAS_AOT_COMPILER)
    # the tree of the game's daScript AOT compiler (DagorDas.cmake): the compiler, with the game's own modules
    # (AOT_SOURCES) and what the libraries of the lists add to it (their _aot.cmake), instead of the game
    set_property(GLOBAL PROPERTY DAGOR_GAME_TARGET "${game}-aot")
    dagor_add_executable(${game}-aot STRICT QUIRREL CONSOLE OUTPUT_DIR "${CMAKE_BINARY_DIR}/bin"
      SOURCES ${arg_AOT_SOURCES}
      PRIVATE_INCLUDES ${DAGOR_DNG_INCLUDES} ${DAGOR_PROG_DIR}/daNetGameLibs ${DAGOR_PROG_DIR}/gameLibs
      DEPS daNetGame-das-aot
    )
    _dagor_dng_lib_files(libs _aot.cmake "${arg_DNG_LIBS}" "${arg_GAME_LIBS}")
    foreach(lib IN LISTS libs)
      include("${lib}")
    endforeach()
    return()
  endif()
  set(gen "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}")

  # gameproj:: (game.jam's DefVars, keys and the like)
  set(text "#include <stddef.h>\n#include <string.h>\nnamespace gameproj\n{\n")
  string(APPEND text "const char *game_codename() { return \"${game}\"; }\n")
  string(APPEND text "const char *main_vromfs_fpath() { return \"${arg_MAIN_VROM}\"; }\n")
  string(APPEND text "const char *main_vromfs_mount_dir() { return \"${vrom_dir}\"; }\n")
  string(APPEND text "const char *game_user_dir_name() { return \"${arg_USER_DIR}\"; }\n")
  string(APPEND text "const char *config_name_prefix() { return \"${game}.config\"; }\n")
  string(APPEND text "const char *game_window_title() { return \"${arg_WINDOW_TITLE}\"; }\n")
  string(APPEND text "const char *game_telemetry_name() { return \"${game}\"; }\n")
  string(APPEND text "const char *game_yup_name() { return \"\"; }\n")
  string(APPEND text "const char *default_statsd_url() { return nullptr; }\n")
  string(APPEND text "const char *crash_report_url() { return nullptr; }\n")
  string(APPEND text "const char *statsd_key() { return \"${game}\"; }\n")
  string(APPEND text "const char *eventlog_agent() { return \"${game}\"; }\n")
  string(APPEND text "const char *default_eventlog_project() { return \"\"; }\n")
  foreach(callback before_init_video init_before_main_loop update_before_dagor_work_cycle post_shutdown_handler
                   reset_game_resources)
    string(APPEND text "void ${callback}() {}\n")
  endforeach()
  # no game public key, no partner keys, no anti-cheat key: what a project without them gets from game.jam
  string(APPEND text "static const unsigned char pubkey_DER[292] = {0};\n")
  string(APPEND text "const unsigned char *public_key_DER() { return pubkey_DER; }\n")
  string(APPEND text "unsigned public_key_DER_len() { return sizeof(pubkey_DER); }\n")
  string(APPEND text "const unsigned char *partner_public_key_DER(int) { return nullptr; }\n")
  string(APPEND text "unsigned partner_public_key_DER_len(int) { return 0; }\n")
  string(APPEND text "unsigned partner_public_keys_count() { return 0; }\n")
  string(APPEND text "static const unsigned char beacSecretServerKey[] = \"BEAC_KEY_NOT_DEFINED\";\n")
  string(APPEND text "const unsigned char *beac_secret_server_key() { return beacSecretServerKey; }\n")
  string(APPEND text "unsigned beac_secret_server_key_len() { return sizeof(beacSecretServerKey); }\n")
  string(APPEND text "} // namespace gameproj\n")
  if(NOT DAGOR_DEDICATED)
    string(APPEND text "extern \"C\"\n{\nconst char *dedicated_server_dll_fn = nullptr;\n}\n")
  endif()
  file(CONFIGURE OUTPUT "${gen}/gameproj.cpp" CONTENT "${text}")

  # the auth keys: the client's own; the dedicated server's for the clients it checks (outside Rel and IRel unless on
  # Linux, as jam built them)
  string(TOUPPER "${DAGOR_PLATFORM}" platform_upper)
  set(text "#include \"net/userid.h\"\n")
  if(arg_AUTH_KEY_${platform_upper})
    list(JOIN arg_AUTH_KEY_${platform_upper} "," key)
    string(APPEND text "net::auth_key_t net::get_platform_auth_key()\n{\n  static const uint8_t key[] = {${key}};\n")
    string(APPEND text "  return auth_key_t(key, sizeof(key));\n}\n")
  else()
    string(APPEND text "net::auth_key_t net::get_platform_auth_key() { return {}; }\n")
  endif()
  if(DAGOR_DEDICATED)
    set(checked "1")
    if(NOT DAGOR_PLATFORM STREQUAL "linux")
      set(checked "DAGOR_DBGLEVEL > 0")
    endif()
    set(pairs ${arg_DEDICATED_AUTH})
    set(keys "")
    set(lookups "")
    set(null_defined OFF)
    while(pairs)
      list(POP_FRONT pairs prefix platform)
      string(TOUPPER "${platform}" upper)
      if(arg_AUTH_KEY_${upper})
        list(JOIN arg_AUTH_KEY_${upper} "," key)
        string(APPEND keys "static const uint8_t bkey_${prefix}[] = {${key}};\n")
        string(APPEND keys "static net::auth_key_t key_${prefix}{bkey_${prefix}, sizeof(bkey_${prefix})};\n")
        string(APPEND lookups "  if (strstr(pltf, \"${prefix}\") == pltf) { out_key = &key_${prefix}; return true; }\n")
      else()
        if(NOT null_defined)
          string(APPEND keys "static net::auth_key_t key_null;\n")
          set(null_defined ON)
        endif()
        string(APPEND lookups "  if (strstr(pltf, \"${prefix}\") == pltf) { out_key = &key_null; return true; }\n")
      endif()
    endwhile()
    string(APPEND text "#if ${checked}\n${keys}#endif\n")
    string(APPEND text "bool net::get_auth_key_for_platform(const char *pltf, net::auth_key_t *&out_key)\n{\n")
    string(APPEND text "  if (strstr(pltf, \"win\") == pltf || strstr(pltf, \"mac\") == pltf) { out_key = nullptr; return true; }\n")
    string(APPEND text "#if ${checked}\n${lookups}#endif\n  return false;\n}\n")
  endif()
  file(CONFIGURE OUTPUT "${gen}/authKeys.cpp" CONTENT "${text}")

  # daNetGame's main and version (compiled here, with the game's include dirs); the GPU switching exports of Windows
  # releases
  file(CONFIGURE OUTPUT "${gen}/gameMain.cpp" CONTENT "#include \"main/main.cpp\"\n")
  file(CONFIGURE OUTPUT "${gen}/gameVersion.cpp" CONTENT "#include \"main/version.cpp\"\n")
  set(sources "${gen}/gameproj.cpp" "${gen}/authKeys.cpp" "${gen}/gameMain.cpp" "${gen}/gameVersion.cpp")
  if(DAGOR_PLATFORM STREQUAL "windows" AND DAGOR_GAME_RENDERER)
    file(CONFIGURE OUTPUT "${gen}/renderOptimus.cpp" CONTENT "#include \"render/opt/optimus.cpp\"\n")
    list(APPEND sources "$<$<CONFIG:Rel,IRel>:${gen}/renderOptimus.cpp>")
  endif()
  if(arg_LOG_CRYPT_KEY AND DAGOR_FORCE_LOGS)
    list(JOIN arg_LOG_CRYPT_KEY "," key)
    file(CONFIGURE OUTPUT "${gen}/logCryptKey.cpp" CONTENT
      "const unsigned char *get_dagor_log_crypt_key()\n{\n  static const unsigned char key[128] = {${key}};\n  return key;\n}\n")
    list(APPEND sources "$<$<CONFIG:Rel,IRel>:${gen}/logCryptKey.cpp>")
  endif()

  # the pull of every module and library of the game, filled in by their dagor_game_lib() calls (pulls of some
  # configurations are $<cond:name>, empty in the others)
  set(pulls "$<FILTER:$<TARGET_PROPERTY:${target},DAGOR_GAME_PULLS>,EXCLUDE,^$>")
  set(bs "\\")
  set(text "#include <daECS/core/componentType.h>\n#define REG_SYS${bs}\n")
  string(APPEND text "$<$<BOOL:${pulls}>:  RS($<JOIN:${pulls},)${bs}\n  RS(>)${bs}\n>\n")
  string(APPEND text "#define RS(x) extern size_t x;\nREG_SYS\n#undef RS\n#define RS(x) + (x)\n")
  string(APPEND text "size_t game_pulls = 0 REG_SYS;\n")
  _dagor_config_generate(sources "${gen}/gamePulls.cpp" "${text}")

  if(arg_CPP_DIRS)
    dagor_glob_sources(sources DIRS ${arg_CPP_DIRS} GLOB *.cpp)
  endif()
  set(es)
  if(arg_ES_DIRS)
    dagor_glob_sources(es DIRS ${arg_ES_DIRS} GLOB *ES.cpp.inl)
  endif()
  set(name "${game}")
  if(DAGOR_DEDICATED)
    set(name "${game}-ded")
  endif()
  dagor_add_executable(${target} STRICT QUIRREL OUTPUT_NAME ${name}
    SOURCES ${sources} ${arg_SOURCES}
    ES_SOURCES ${es} ${arg_ES_SOURCES}
    ${forward}
  )
  set_property(TARGET ${target} APPEND PROPERTY DAGOR_GAME_PULLS ${arg_PULLS})
  target_include_directories(${target} PRIVATE ${DAGOR_DNG_INCLUDES})
  target_compile_options(${target} PRIVATE ${DAGOR_DNG_OPTIONS})
  # main/main.cpp, compiled here, shows the splash screen
  set(splash gameLibs/render/animatedSplashScreen)
  if(NOT DAGOR_GAME_RENDERER)
    set(splash gameLibs/render/animatedSplashScreen/stub)
  endif()
  dagor_game_lib(DEPS ${splash} INCLUDES "${DAGOR_PROG_DIR}/gameLibs/render/animatedSplashScreen/public_api")

  # what the daNetGameLibs and gameLibs of the lists add to the game: their _lib.cmake (dagor_game_lib)
  _dagor_dng_lib_files(libs _lib.cmake "${arg_DNG_LIBS}" "${arg_GAME_LIBS}")
  foreach(lib IN LISTS libs)
    include("${lib}")
  endforeach()
endfunction()
