options gen2
require ecs
require math.base
require DagorMath
require danetlibs/test_harness/ecs_test

// In-game tests: python project.py test -k dng_empty.ecs (see test.blk next to this file)

[ecs_test]
def spinner_turns_at_its_speed(t : T?) {
  let eid = createEntitySync("spinner") <| $(var init) {
    set(init, "spinner__speed", PI) // half a turn per second
  }
  advance_frames(60) // a second: every frame advances the game by test_mode_fixed_dt() = 1/60
  let tm = get_TMatrix(eid, "transform") ?? IDENT_TM
  t |> success(abs(tm[0].x - -1.0) < 1e-3, "half a turn: the x axis points backwards, got {tm[0]}")
  destroyEntity(eid)
}

[ecs_test]
def the_scene_has_the_default_world(t : T?) {
  var levels = 0
  query() <| $ [es] (level__blk : string) {
    t |> equal(level__blk, "__default__")
    levels++
  }
  t |> equal(levels, 1, "one level entity")
}
