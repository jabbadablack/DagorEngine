options gen2
require ecs
require danetlibs/test_harness/scenario

// Scenario tests render with the client game: python test_all.py run --project outerSpace -k outerSpace.scenarios
// Reference images are in references/; recreate them with --update-references after an intended visual change.

[ecs_test]
def empty_scene_renders(t : T?) {
  advance_frames(60) // let exposure and temporal effects settle
  check_screenshot(t, "empty_scene")
}

[ecs_test]
def unknown_input_actions_fail_loudly(t : T?) {
  t |> run("send_action") <| @(t : T?) {
    t |> success(get_action_handle("no.such.action", uint16(0xFFFF)) == BAD_ACTION_HANDLE)
  }
}
