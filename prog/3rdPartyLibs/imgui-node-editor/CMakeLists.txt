# imgui-node-editor: node graph widgets for ImGui
set(includes ${CMAKE_CURRENT_SOURCE_DIR} ${DAGOR_PROG_DIR}/3rdPartyLibs/imgui)
set(sources crude_json.cpp imgui_canvas.cpp imgui_node_editor_api.cpp imgui_node_editor.cpp)
list(APPEND deps 3rdPartyLibs/imgui)

dagor_add_library(SOURCES ${sources} PRIVATE_INCLUDES ${includes} DEPS ${deps})
