# Content built by the tree's tools.
#
# dagor_add_shaders(<name> COMPILER <dsc2 target> BLK <shaders.blk> OUTPUT <dir>/<base> [ARGS <compiler args>...]
#                   [INSTALL <dir> COMPONENT <component>])
# A target that compiles the shaders of <shaders.blk> with a shader compiler of the tree (dsc2-dx12, ...) into the
# dumps <dir>/<base>.<profile>.shdump.bin, when the compiler or a shader source changes (the .dshl/.hlsl files of the
# blk's dir and of its incDir dirs). It runs in the blk's dir, as the shader scripts did; the intermediate files go to
# the build dir. INSTALL also installs the dumps into <dir> of the install prefix.
include_guard(GLOBAL)

function(dagor_add_shaders name)
  cmake_parse_arguments(PARSE_ARGV 1 arg "" "COMPILER;BLK;OUTPUT;INSTALL;COMPONENT" "ARGS")
  foreach(required COMPILER BLK OUTPUT)
    if(NOT arg_${required})
      message(FATAL_ERROR "dagor_add_shaders(${name}): ${required} is required")
    endif()
  endforeach()
  _dagor_abs_paths(blk "${arg_BLK}")
  cmake_path(GET blk PARENT_PATH blk_dir)
  cmake_path(GET arg_OUTPUT PARENT_PATH out_dir)
  cmake_path(GET arg_OUTPUT FILENAME out_base)

  # the shader sources: the blk's dir and its incDir:t="..." dirs
  set(dirs "${blk_dir}")
  file(STRINGS "${blk}" inc_lines REGEX "^[ \t]*incDir:t[ \t]*=")
  foreach(line IN LISTS inc_lines)
    if(line MATCHES "\"([^\"]+)\"")
      cmake_path(ABSOLUTE_PATH CMAKE_MATCH_1 BASE_DIRECTORY "${blk_dir}" NORMALIZE OUTPUT_VARIABLE dir)
      list(APPEND dirs "${dir}")
    endif()
  endforeach()
  set(patterns)
  foreach(dir IN LISTS dirs)
    list(APPEND patterns "${dir}/*.dshl" "${dir}/*.hlsl" "${dir}/*.hlsli" "${dir}/*.sh")
  endforeach()
  file(GLOB_RECURSE shader_sources CONFIGURE_DEPENDS ${patterns})

  set(work "${CMAKE_CURRENT_BINARY_DIR}/shaders/${name}")
  set(stamp "${work}/${name}.stamp")
  add_custom_command(OUTPUT "${stamp}"
    COMMAND "${CMAKE_COMMAND}" -E make_directory "${out_dir}"
    COMMAND "$<TARGET_FILE:${arg_COMPILER}>" "${blk}" -out "${arg_OUTPUT}" -q -shaderOn -nodisassembly -commentPP
      -codeDumpErr ${arg_ARGS} -o "${work}/obj"
    COMMAND "${CMAKE_COMMAND}" -E touch "${stamp}"
    WORKING_DIRECTORY "${blk_dir}"
    DEPENDS "${blk}" ${shader_sources} ${arg_COMPILER}
    COMMENT "Compiling the shaders of ${name} (${arg_COMPILER})"
    VERBATIM)
  add_custom_target(${name} ALL DEPENDS "${stamp}")
  set_property(TARGET ${name} PROPERTY FOLDER "shaders")
  if(arg_INSTALL)
    if(NOT arg_COMPONENT)
      message(FATAL_ERROR "dagor_add_shaders(${name}): INSTALL needs a COMPONENT")
    endif()
    install(DIRECTORY "${out_dir}/" DESTINATION "${arg_INSTALL}" COMPONENT "${arg_COMPONENT}"
      FILES_MATCHING PATTERN "${out_base}.*.shdump.bin")
  endif()
endfunction()
