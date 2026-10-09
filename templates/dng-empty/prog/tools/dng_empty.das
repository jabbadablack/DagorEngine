options gen2
options no_aot = true
require ecs.fs
require %toolScripts/_libs_init // load_libs(): the libs in prog/danetgamelibs.txt, written by setup

// What daEditor runs to render levels like the game does (application.blk game{ daNetGameEditorRender:b=yes }): it
// replaces the game's entry script (settings.blk game_das_script:t=), so it loads only what the editor needs.
// python build.py tools copies this dir into the editor's snapshot (application.blk dngSnapshot:t=).
[init]
def load {
  load_libs()
  load_folder("%scripts/dng_empty/es")
}
