# CMAKE_USER_MAKE_RULES_OVERRIDE (set by DagorBootstrap.cmake): CMake runs it after a language's platform defaults and
# before they initialize the CMAKE_<LANG>_FLAGS* cache entries. It drops those defaults (/GR /EHsc /W3 /DWIN32 -O2 -g
# and the per-config ones) so that every compile and link flag comes from Dagor::BuildSettings, apart from what the
# toolchain file needs for the compiler to work at all (DAGOR_TOOLCHAIN_<LANG>_FLAGS, DAGOR_TOOLCHAIN_LINKER_FLAGS).

foreach(_dagor_lang C CXX OBJC OBJCXX ASM ASM_NASM ASM_MASM RC)
  set(CMAKE_${_dagor_lang}_FLAGS_INIT "${DAGOR_TOOLCHAIN_${_dagor_lang}_FLAGS}")
  foreach(_dagor_cfg DEBUG RELEASE RELWITHDEBINFO MINSIZEREL DEV REL IREL DBG)
    set(CMAKE_${_dagor_lang}_FLAGS_${_dagor_cfg}_INIT "")
  endforeach()
  set(CMAKE_${_dagor_lang}_STANDARD_LIBRARIES_INIT "")
endforeach()

foreach(_dagor_kind EXE SHARED MODULE STATIC)
  if(_dagor_kind STREQUAL "STATIC")
    set(CMAKE_${_dagor_kind}_LINKER_FLAGS_INIT "")
  else()
    set(CMAKE_${_dagor_kind}_LINKER_FLAGS_INIT "${DAGOR_TOOLCHAIN_LINKER_FLAGS}")
  endif()
  foreach(_dagor_cfg DEBUG RELEASE RELWITHDEBINFO MINSIZEREL DEV REL IREL DBG)
    set(CMAKE_${_dagor_kind}_LINKER_FLAGS_${_dagor_cfg}_INIT "")
  endforeach()
endforeach()
unset(_dagor_lang)
unset(_dagor_cfg)
unset(_dagor_kind)
