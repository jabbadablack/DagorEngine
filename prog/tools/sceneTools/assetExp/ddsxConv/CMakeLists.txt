# The DDSx texture converter plugins of daBuild and the tools (plugins/ddsx): pcDdsxConv (PC formats), iosDdsxConv and
# andDdsxConv (the mobile formats of iOS and Android). jam built them rel only, so without a config suffix.
foreach(plugin pc ios and)
  set(defines)
  if(plugin STREQUAL "ios")
    set(defines IOS_EXP BUILD_FOR_MOBILE_TEXFMT)
  elseif(plugin STREQUAL "and")
    set(defines TEGRA_EXP BUILD_FOR_MOBILE_TEXFMT)
  endif()
  dagor_add_shared_library(${plugin}DdsxConv CDK_SUBDIR plugins/ddsx NO_CONFIG_POSTFIX
    OUTPUT_DIR ${CMAKE_BINARY_DIR}/bin/plugins/ddsx
    SOURCES ddsxConvPc.cpp main_mem.cpp
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude ${DAGOR_PROG_DIR}/tools/sharedInclude
    PRIVATE_DEFINES ${defines}
  )
endforeach()
