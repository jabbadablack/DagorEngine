options gen2
require ecs
require AppTime
require DagorSystem
require danetlibs/test_harness/ecs_test

// In-game tests: run with `python test_all.py run --project outerSpace -k outerSpace.ecs` (see test.blk next to this file)

[ecs_test]
def entities_are_created_and_destroyed(t : T?) {
  let eid = createEntitySync("static_cam")
  t |> success(doesEntityExist(eid), "the entity exists right after creation")
  t |> equal(getEntityTemplateName(eid), "static_cam")
  destroyEntity(eid)
  advance_frames(1)
  t |> success(!doesEntityExist(eid), "destroyed entities are gone after a frame")
}

[ecs_test]
def every_frame_advances_by_the_fixed_dt(t : T?) {
  let before = get_sync_time()
  advance_frames(60)
  t |> numericEqual(float(get_sync_time() - before), 60.0 * test_mode_fixed_dt(), "game time after 60 frames")
}

[ecs_test]
def expected_errors_do_not_fail_the_test(t : T?) {
  t |> expect_logerr("expected test error", 1) <| $() {
    logerr("expected test error")
  }
}

[ecs_test]
def sub_tests_are_reported_separately(t : T?) {
  t |> run("first") <| @(t : T?) {
    t |> equal(2, 1 + 1)
  }
  t |> run("second") <| @(t : T?) {
    t |> success(advance_until(t, 10) <| $() { return true; })
  }
}
