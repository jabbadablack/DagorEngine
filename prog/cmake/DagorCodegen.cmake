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
  endforeach()
  target_sources(${target} PRIVATE ${outputs})
  target_include_directories(${target} PRIVATE "${gen_dir}")
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
