# The engine's ImGui integration: platform input, the renderer, the test runtime, netImgui outside Rel. Programs that
# set DAGOR_IMGUI_TEST_ENGINE get the build with the ImGui test engine hooks (see 3rdPartyLibs/imgui).
include(netImgui.cmake)
set(sources imguiImpl.cpp imguiRenderer.cpp imguiTestRuntime.cpp)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources imgui_impl_win32.cpp)
elseif(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources imgui_impl_osx.mm)
else()
  list(APPEND sources imgui_impl_stub.cpp)
endif()
foreach(build standard testEngine)
  set(defines ${NET_IMGUI_DEFINES})
  if(build STREQUAL "testEngine")
    list(APPEND defines IMGUI_ENABLE_TEST_ENGINE)
  endif()
  dagor_add_library(engine.imgui.${build}
    SOURCES ${sources}
    PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/engine/sharedInclude ${NET_IMGUI_INCLUDES}
    PRIVATE_DEFINES ${defines}
    DEPS 3rdPartyLibs/imgui ${NET_IMGUI_DEPS}
  )
endforeach()
dagor_add_link_choice(engine.imgui PROPERTY DAGOR_IMGUI_TEST_ENGINE ON engine.imgui.testEngine OFF engine.imgui.standard)
