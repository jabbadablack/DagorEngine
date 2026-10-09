options gen2
require ecs
require danetlibs/test_harness/scenario

// python ../../../project.py test -k dng_empty.scenarios
// References are in references/; recreate them with --update-references after an intended visual change and review them.

[ecs_test]
def the_default_world_renders(t : T?) {
  advance_frames(60) // let exposure and temporal effects settle
  check_screenshot(t, "default_world")
}
