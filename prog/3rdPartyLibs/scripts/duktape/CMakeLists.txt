# Duktape 2.2.1, the embeddable ECMAScript engine, built as its command line interpreter (duktape)
set(includes examples/cmdline src)
set(sources src/duktape.c examples/cmdline/duk_cmdline.c)
set(defines __B_NO_MEM_BASE_INCLUDE)
list(APPEND defines DUK_CMDLINE_PRINTALERT_SUPPORT)
list(APPEND includes extras/print-alert)
list(APPEND sources extras/print-alert/duk_print_alert.c)
list(APPEND defines DUK_CMDLINE_CONSOLE_SUPPORT)
list(APPEND includes extras/console)
list(APPEND sources extras/console/duk_console.c)
list(APPEND defines DUK_CMDLINE_LOGGING_SUPPORT)
list(APPEND includes extras/logging)
list(APPEND sources extras/logging/duk_logging.c)
list(APPEND defines DUK_CMDLINE_MODULE_SUPPORT)
list(APPEND includes extras/module-duktape)
list(APPEND sources extras/module-duktape/duk_module_duktape.c)
list(APPEND defines DUK_CMDLINE_FILEIO)
if(DAGOR_PLATFORM MATCHES "^(linux|macOS)$")
  list(APPEND options -fno-fast-math -Wno-format-overflow)
endif()

dagor_add_executable(duktape CONSOLE
  CDK
  NO_CONFIG_POSTFIX
  SOURCES ${sources}
  PRIVATE_INCLUDES ${includes}
  PRIVATE_DEFINES ${defines}
  COMPILE_OPTIONS ${options}
)
