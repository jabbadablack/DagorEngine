# The Quirrel compiler and static analyzer (with exceptions); the engine's build replaces upstream's CMakeLists.txt
set(defines)
if(DAGOR_SQ_VAR_TRACE)
  list(APPEND defines SQ_VAR_TRACE_ENABLED)
endif()
dagor_add_library(QUIRREL_HEADERS EXCEPTIONS ON
  SOURCES
    ast.cpp
    compilationcontext.cpp
    parser.cpp
    codegen.cpp
    typeinference.cpp
    constgen.cpp
    compiler.cpp
    sqfuncstate.cpp
    sqdump.cpp
    optimizer.cpp
    lexer.cpp
    sqtypeparser.cpp
    optimizations/closureHoisting.cpp
    static_analyzer/analyzer.cpp
    static_analyzer/checker_visitor.cpp
    static_analyzer/name_shadowing_checker.cpp
    static_analyzer/function_ret_type_eval.cpp
    static_analyzer/config.cpp
    static_analyzer/var_scope.cpp
    static_analyzer/value_ref.cpp
    static_analyzer/naming.cpp
    static_analyzer/global_state.cpp
    static_analyzer/external_value.cpp
  PRIVATE_INCLUDES .. . ../../helpers ../../internal
  PRIVATE_DEFINES ${defines}
  DEPS 3rdPartyLibs/eastl
)
