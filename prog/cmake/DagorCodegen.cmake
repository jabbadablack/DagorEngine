# Sources generated at build time.
#
# STRINGIFY / STRINGIFY_ARRAY of dagor_add_*: <file>.inl with the file's text as a C string literal (or a byte array),
# for embedding scripts such as daScript modules (#include "<file>.inl"). The .inl files are written to the build dir,
# which is added to the target's include dirs.
include_guard(GLOBAL)

set(DAGOR_STRINGIFY_SCRIPT "${DAGOR_PROG_DIR}/_jBuild/_scripts/stringify.py")

# _dagor_stringify(<target> <mode> <file>...): mode is "" (string) or --array
function(_dagor_stringify target mode)
  _dagor_base_dir(base)
  set(gen_dir "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}")
  set(outputs)
  set(dirs)
  foreach(file IN LISTS ARGN)
    _dagor_abs_paths(src "${file}")
    cmake_path(RELATIVE_PATH src BASE_DIRECTORY "${base}" OUTPUT_VARIABLE rel)
    set(out "${gen_dir}/${rel}.inl")
    add_custom_command(OUTPUT "${out}"
      COMMAND "${Python3_EXECUTABLE}" "${DAGOR_STRINGIFY_SCRIPT}" ${mode} "${src}" "${out}"
      # jam wrote the .inl next to the source, where a quoted #include would find a stale one first
      COMMAND "${CMAKE_COMMAND}" -E rm -f "${src}.inl"
      DEPENDS "${src}" "${DAGOR_STRINGIFY_SCRIPT}"
      COMMENT "Stringifying ${rel}"
      VERBATIM)
    list(APPEND outputs "${out}")
    # the sources include it by its name, as from their own dir
    cmake_path(GET out PARENT_PATH out_dir)
    list(APPEND dirs "${out_dir}")
  endforeach()
  list(REMOVE_DUPLICATES dirs)
  target_sources(${target} PRIVATE ${outputs})
  target_include_directories(${target} PRIVATE "${gen_dir}" ${dirs})
endfunction()

# dagor_legacy_parsers(<target> [LEX <file>.dlp...] [SYN <file>.whl...]): the shader compilers' lexers (dolphin:
# <file>.cpp, <file>.h) and LR parsers (whale: <file>.cpp, <file>.h, <file>tok.h), generated into the build dir by
# dolphin and whale (prog/3rdPartyLibs/legacy_parser; the tree's own, the host's when cross-compiling) and compiled
# into <target>
function(dagor_legacy_parsers target)
  cmake_parse_arguments(PARSE_ARGV 1 arg "" "" "LEX;SYN")
  _dagor_base_dir(base)
  set(gen_dir "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/parsers")
  set(sources)
  foreach(kind LEX SYN)
    foreach(file IN LISTS arg_${kind})
      _dagor_abs_paths(src "${file}")
      cmake_path(GET src STEM stem)
      cmake_path(GET src FILENAME name)
      if(kind STREQUAL "LEX")
        set(tool dolphin)
        set(suffixes .cpp .h)
      else()
        set(tool whale)
        set(suffixes .cpp .h tok.h)
      endif()
      dagor_host_tool(${tool} tool_path DIR 3rdPartyLibs/legacy_parser/${tool})
      set(outputs)
      set(stale)
      foreach(suffix IN LISTS suffixes)
        list(APPEND outputs "${gen_dir}/${stem}${suffix}")
        cmake_path(GET src PARENT_PATH src_dir)
        list(APPEND stale "${src_dir}/${stem}${suffix}")
      endforeach()
      add_custom_command(OUTPUT ${outputs}
        COMMAND "${CMAKE_COMMAND}" -E copy_if_different "${src}" "${gen_dir}/${name}"
        COMMAND "${tool_path}" "${name}"
        # jam wrote them next to the grammar, where a quoted #include would find a stale one first
        COMMAND "${CMAKE_COMMAND}" -E rm -f ${stale}
        WORKING_DIRECTORY "${gen_dir}"
        DEPENDS "${src}" ${tool_path_DEPENDS}
        COMMENT "Generating ${name} (${tool})"
        VERBATIM)
      list(APPEND sources ${outputs})
    endforeach()
  endforeach()
  file(MAKE_DIRECTORY "${gen_dir}")
  target_sources(${target} PRIVATE ${sources})
  target_include_directories(${target} PRIVATE "${gen_dir}")
endfunction()

# _dagor_es_codegen(<target> <file>ES.cpp.inl...): the registration code of the entity systems (ES_SOURCES), made by
# prog/_jBuild/_scripts/gen_es.py (libclang) from each .inl with the target's own definitions and include dirs, and
# compiled into <target>. It goes into the build dir; the generated file includes the .inl by its name, as the
# committed ones do, through a forwarding file next to it.
function(_dagor_es_codegen target)
  dagor_python(python)
  set(llvm "${DAGOR_LLVM_DIR}")
  if(NOT llvm)
    dagor_fetch_sdk(llvm llvm) # libclang, for trees built with GCC
  endif()
  set(scripts "${DAGOR_PROG_DIR}/_jBuild/_scripts")
  set(gen_dir "${CMAKE_CURRENT_BINARY_DIR}/gen/${target}/es")
  # the compiler's arguments the parse needs, per configuration (the C++ ones)
  set(defines "$<TARGET_PROPERTY:${target},COMPILE_DEFINITIONS>")
  set(includes "$<TARGET_PROPERTY:${target},INCLUDE_DIRECTORIES>")
  set(content "$<$<BOOL:${defines}>:-D$<JOIN:${defines},\n-D>\n>$<$<BOOL:${includes}>:-I$<JOIN:${includes},\n-I>\n>")
  foreach(header IN LISTS DAGOR_FORCED_INCLUDES)
    string(APPEND content "-include\n${header}\n")
  endforeach()
  # the system headers, which the toolchain gives the compiler by other means: clang's own, MSVC's and the SDK's
  file(GLOB clang_builtins LIST_DIRECTORIES true "${llvm}/lib/clang/*/include")
  set(system_dirs ${clang_builtins})
  if(DAGOR_PLATFORM STREQUAL "windows")
    set(sdk_inc "${DAGOR_WINSDK_DIR}/Include/${DAGOR_WINSDK_RESOLVED_VERSION}")
    list(APPEND system_dirs "${DAGOR_MSVC_DIR}/include" "${sdk_inc}/ucrt" "${sdk_inc}/um" "${sdk_inc}/shared")
  endif()
  foreach(dir IN LISTS system_dirs)
    string(APPEND content "-imsvc\n${dir}\n")
  endforeach()
  file(GENERATE OUTPUT "${gen_dir}/args-$<CONFIG>-$<COMPILE_LANGUAGE>.txt" CONTENT "${content}" TARGET ${target})
  set(args "${gen_dir}/args-$<CONFIG>-CXX.txt")

  set(sources)
  foreach(src IN LISTS ARGN)
    _dagor_config_source("${src}" cond path) # $<cond:path>: generated always, compiled where cond holds
    if(path)
      set(src "${path}")
    endif()
    cmake_path(GET src FILENAME name)
    string(REGEX REPLACE "\\.[^.]+$" ".gen.es.cpp" out_name "${name}") # <name>ES.cpp.inl, or a .cpp it includes
    set(out "${gen_dir}/${out_name}")
    file(CONFIGURE OUTPUT "${gen_dir}/${name}" CONTENT "#include \"${src}\"\n")
    # the descriptors record the source relative to the engine root, as jam ran it (absolute on another drive)
    cmake_path(RELATIVE_PATH src BASE_DIRECTORY "${DAGOR_ENGINE_ROOT}" OUTPUT_VARIABLE input)
    if(IS_ABSOLUTE "${input}")
      set(input "${src}")
    endif()
    add_custom_command(OUTPUT "${out}"
      COMMAND "${CMAKE_COMMAND}" -E env "DAGOR_CLANG_DIR=${llvm}"
        "${python}" "${scripts}/gen_es.py" "${input}" "${out}" "${name}" "@${args}"
      # gen_es.py leaves an unchanged output as it was: newer than its inputs now, it is not made again
      COMMAND "${CMAKE_COMMAND}" -E touch_nocreate "${out}"
      DEPENDS "${src}" "${args}" "${scripts}/gen_es.py" "${scripts}/gen_es30.py" "${scripts}/clang_ecs_parser.py"
      WORKING_DIRECTORY "${DAGOR_ENGINE_ROOT}"
      COMMENT "ES codegen: ${name}"
      VERBATIM)
    if(cond)
      set(out "$<${cond}:${out}>")
    endif()
    list(APPEND sources "${out}")
  endforeach()
  target_sources(${target} PRIVATE ${sources})
endfunction()
