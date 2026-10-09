options gen2
options no_aot = true // a loader: the scripts it loads are compiled ahead of time (jamfile AllSrcFolder_DAS)
require app
require ecs.fs
require %scripts/_libs_init // load_libs(): the libs in prog/danetgamelibs.txt, written by setup

// The game's das entry point (settings.blk game_das_script:t=): loads every script of the game
[init]
def load {
  var ok = load_libs()
  ok = load_folder("%scripts/dng_empty/es") && ok
  if (is_in_aot()) {
    assert(ok)
  }
}
