# daScript compiled ahead of time (DAGOR_DAS_AOT, game trees): the DAS_AOT files of dagor_add_* are translated to C++
# by the game's AOT compiler and compiled into the target, in batches of 10 (jam's AotCompileBatchedGeneratedDAS).
#
# The AOT compiler is a host program of the game (daNetGame-das-aot with the game's daScript modules), built by a
# sub-build of the game's own source tree with DAGOR_DAS_AOT_COMPILER (see dagor_add_dng_game): target
# dagor.dasAotCompiler configures <game>/build/_host/aot-<host> once and builds it under a lock, in Dev, as jam did.
# DAGOR_DAS_AOT_COMPILER_PATH names a prebuilt one instead.
#
# Each batch defines aot_<batch>_pull; DAS_AOT_PULL <name> of the target is the variable that references them all
# (in a program: just defined), which the code that pulls the target's daScript in names (e.g. ecs_aot_DAS_pull_AOT
# of gameLibs/das/ecs).
include_guard(GLOBAL)

set(DAGOR_DAS_AOT_COMPILER_PATH "" CACHE FILEPATH "A prebuilt daScript AOT compiler of the game; empty builds it")
set(DAGOR_DAS_AOT_BATCH 10 CACHE STRING "daScript files per AOT-compiled C++ batch")
set(DAGOR_DAS_AOT_SCRIPT "${CMAKE_CURRENT_LIST_DIR}/scripts/build_das_aot_compiler.cmake")

# _dagor_das_aot_compiler(<out-var>): the compiler to run, and <out-var>_DEPENDS
function(_dagor_das_aot_compiler out)
  if(DAGOR_DAS_AOT_COMPILER_PATH)
    set(${out} "${DAGOR_DAS_AOT_COMPILER_PATH}" PARENT_SCOPE)
    set(${out}_DEPENDS "${DAGOR_DAS_AOT_COMPILER_PATH}" PARENT_SCOPE)
    return()
  endif()
  get_property(game GLOBAL PROPERTY DAGOR_GAME_CODENAME)
  if(NOT game)
    message(FATAL_ERROR "daScript AOT (DAGOR_DAS_AOT) needs the tree's game (dagor_add_dng_game)")
  endif()
  set(tree "${CMAKE_SOURCE_DIR}/build/_host/aot-${DAGOR_HOST_TAG}")
  set(exe "${tree}/bin/${game}-aot-dev")
  if(CMAKE_HOST_WIN32)
    string(APPEND exe ".exe")
  endif()
  if(NOT TARGET dagor.dasAotCompiler)
    set(make_program "")
    if(CMAKE_GENERATOR MATCHES "Ninja")
      set(make_program "${CMAKE_MAKE_PROGRAM}")
    endif()
    add_custom_target(dagor.dasAotCompiler
      COMMAND "${CMAKE_COMMAND}" -DSOURCE_DIR=${CMAKE_SOURCE_DIR} -DTREE=${tree} -DTARGET=${game}-aot
        -DENGINE_ROOT=${DAGOR_ENGINE_ROOT} -DDEPS_DIR=${DAGOR_DEPS_DIR} -DMAKE_PROGRAM=${make_program}
        -P "${DAGOR_DAS_AOT_SCRIPT}"
      BYPRODUCTS "${exe}"
      COMMENT "daScript AOT compiler of ${game} (${DAGOR_HOST_TAG}, Dev)"
      USES_TERMINAL
      VERBATIM)
    set_property(TARGET dagor.dasAotCompiler PROPERTY FOLDER "tools")
  endif()
  set(${out} "${exe}" PARENT_SCOPE)
  set(${out}_DEPENDS dagor.dasAotCompiler "${exe}" PARENT_SCOPE)
endfunction()

# _dagor_das_aot(<target> <pull> <file>.das...)
function(_dagor_das_aot target pull)
  if(NOT pull)
    message(FATAL_ERROR "${target}: DAS_AOT needs DAS_AOT_PULL, the name of the variable that pulls its daScript in")
  endif()
  _dagor_das_aot_compiler(compiler)
  get_property(work_dir GLOBAL PROPERTY DAGOR_DAS_AOT_DIR) # the game's prog dir: its aot_config.blk
  _dagor_base_dir(base)
  set(gen "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/das/$<CONFIG>")
  get_target_property(type ${target} TYPE)
  _dagor_abs_paths(files ${ARGN})

  set(batch_index 0)
  set(anchors)
  set(sources)
  while(files)
    list(LENGTH files n)
    if(n GREATER DAGOR_DAS_AOT_BATCH)
      set(n ${DAGOR_DAS_AOT_BATCH})
    endif()
    list(SUBLIST files 0 ${n} batch)
    list(SUBLIST files ${n} -1 files)

    set(args)
    set(outputs)
    set(text "")
    foreach(src IN LISTS batch)
      cmake_path(RELATIVE_PATH src BASE_DIRECTORY "${base}" OUTPUT_VARIABLE rel)
      string(REGEX REPLACE "\\.das$" "_das_AOT.cpp" rel "${rel}")
      string(REPLACE "../" "__/" rel "${rel}")
      list(APPEND args -aot "${src}" "${gen}/${rel}")
      list(APPEND outputs "${gen}/${rel}")
      string(APPEND text "#include \"${gen}/${rel}\"\n")
    endforeach()
    set(name "das_batch_${target}_${batch_index}")
    string(MAKE_C_IDENTIFIER "${name}" anchor)
    string(APPEND text "size_t aot_${anchor}_pull = (size_t)&aot_${anchor}_pull;\n")
    list(APPEND anchors "aot_${anchor}_pull")
    add_custom_command(OUTPUT ${outputs}
      COMMAND "${compiler}" "${DAGOR_PROG_DIR}/1stPartyLibs/daScript/utils/aot/main.das"
        -- --config aot_config.blk -sConfig "$<LOWER_CASE:$<CONFIG>>"
        -force-overwrite -gen1 true -gen2-make true ${args}
      DEPENDS ${batch} ${compiler_DEPENDS}
      WORKING_DIRECTORY "${work_dir}"
      COMMENT "daScript AOT: ${name}"
      VERBATIM)
    set_source_files_properties(${outputs} PROPERTIES HEADER_FILE_ONLY ON)
    list(APPEND sources ${outputs})
    _dagor_config_generate(sources "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/das/${name}.cpp"
      "#include <stddef.h>\n${text}")
    math(EXPR batch_index "${batch_index} + 1")
  endwhile()

  # the target's pull: a library keeps only the objects something references, a program has them all
  if(NOT anchors OR type STREQUAL "EXECUTABLE" OR type STREQUAL "SHARED_LIBRARY")
    set(text "#include <stddef.h>\nsize_t ${pull} = 0;\n")
  else()
    list(JOIN anchors ", " externs)
    list(JOIN anchors " + " sum)
    set(text "#include <stddef.h>\nextern size_t ${externs};\nsize_t ${pull} = 0 + ${sum};\n")
  endif()
  file(CONFIGURE OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/das/${pull}.cpp" CONTENT "${text}")
  list(APPEND sources "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/das/${pull}.cpp")
  target_sources(${target} PRIVATE ${sources})
  target_include_directories(${target} PRIVATE ${DAGOR_PROG_DIR}/1stPartyLibs/daScript/include)
endfunction()
