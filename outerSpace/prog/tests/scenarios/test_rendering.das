options gen2
require ecs
require DngCamera
require danetlibs/test_harness/scenario

// Scenario tests render with the client game: python dng.py test run --project outerSpace -k outerSpace.scenarios
// Reference images are in references/; recreate them with --update-references after an intended visual change.

[ecs_test]
def default_world_renders(t : T?) {
  // the game spawns the player's ship and follows it with its camera; the ship's physics phase depends on how long
  // loading took, so the frame is taken from the scene's static camera, which sees only the world
  var staticCam = INVALID_ENTITY_ID
  find_query() <| $ [es(REQUIRE=camera_view)] (eid : EntityId) {
    if (getEntityTemplateName(eid) == "static_cam") {
      staticCam = eid
      return true
    }
    return false
  }
  if (!t |> success(staticCam != INVALID_ENTITY_ID, "the scene has a static_cam")) {
    return
  }
  t |> success(advance_until(t, 300) <| $() { return get_cur_cam_entity() != staticCam; }, "the game takes over the camera")
  set_scene_camera_entity(staticCam)
  advance_frames(60) // let exposure and temporal effects settle
  check_screenshot(t, "default_world")
}

[ecs_test]
def unknown_input_actions_fail_loudly(t : T?) {
  t |> run("send_action") <| @(t : T?) {
    t |> success(get_action_handle("no.such.action", uint16(0xFFFF)) == BAD_ACTION_HANDLE)
  }
}
