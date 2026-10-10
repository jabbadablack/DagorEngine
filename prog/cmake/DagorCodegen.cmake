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
