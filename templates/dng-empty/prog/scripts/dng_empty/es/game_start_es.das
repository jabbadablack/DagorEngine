options gen2
require app
require ecs
require DagorSystem
require DagorDataBlock

// Once the game is up, it loads its scene: -scene:<path>, else settings.blk scene:t=
// (a game with a menu would switch to its menu scene here, and to a level scene when the player starts one)
[es(on_event=EventOnGameAppStarted)]
def game_start_es(evt : Event) {
  var scene = dgs_get_argv("scene")
  if (empty(scene)) {
    scene = dgs_get_settings() |> datablock_getStr("scene", "")
  }
  print("starting scene {scene}")
  switch_scene(scene)
}
