# The web view plugin of webui: the files of vue/ served from the program, each embedded as a byte array by
# make_serve_cpp.py, which writes the plugin table (webui::webview_files_http_plugins) and the arrays into the build
dagor_python(python)
set(folders
  vue
  vue/components
  vue/core
  vue/vendor
  vue/vendor/font-awesome/css
  vue/vendor/font-awesome/fonts
)
set(served)
foreach(pattern *.vue *.eot *.svg *.ttf *.woff *.woff2 *.js *.css *.html) # in jam's order, the plugin table's
  foreach(folder IN LISTS folders)
    file(GLOB files RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}" CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/${folder}/${pattern}")
    list(SORT files)
    list(APPEND served ${files})
  endforeach()
endforeach()
set(gen "${CMAKE_CURRENT_BINARY_DIR}/gen/serve")
set(script "${CMAKE_CURRENT_SOURCE_DIR}/make_serve_cpp.py")
list(TRANSFORM served PREPEND "${CMAKE_CURRENT_SOURCE_DIR}/" OUTPUT_VARIABLE served_paths)
add_custom_command(OUTPUT "${gen}/ServeFiles.cpp"
  COMMAND "${python}" "${script}" "${gen}/ServeFiles.cpp" ${served}
  DEPENDS ${served_paths} "${script}" "${DAGOR_STRINGIFY_SCRIPT}"
  COMMENT "Embedding the web view files"
  VERBATIM)
file(MAKE_DIRECTORY "${gen}")

dagor_add_library(STRICT
  SOURCES webViewPlugin.cpp "${gen}/ServeFiles.cpp"
  PRIVATE_INCLUDES ${DAGOR_PROG_DIR}/gameLibs/publicInclude ${DAGOR_PROG_DIR}/dagorInclude "${gen}"
  STRINGIFY_ARRAY vue/index.html
)
