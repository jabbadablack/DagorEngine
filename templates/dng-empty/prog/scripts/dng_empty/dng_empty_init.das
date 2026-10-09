options gen2
options no_aot = true
require app
require ecs
require DagorSystem

// Loaded before the game scripts (settings.blk game_das_script_init:t=): the das linter checks them in development
[init]
def load {
  var ok = true
  if (is_in_aot() || (get_DAGOR_DBGLEVEL() > 0 && get_TARGET_PC() != 0 && find_index(get_command_line_arguments(), "--das-no-linter") == -1)) {
    ok = load_das("%danetlibs/dascript_base/linter.das") && ok
  }
  if (is_in_aot()) {
    assert(ok)
  }
}
