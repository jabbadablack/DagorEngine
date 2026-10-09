options gen2
options indenting = 2
options no_aot
options strict_smart_pointers

module scenario shared public

//! Functional (scenario) tests: [ecs_test] functions run by the client game (layer:t="scenario" in test.blk), which drive
//! the game like a player would and check what's on screen:
//!
//!   require danetlibs/test_harness/scenario
//!
//!   [ecs_test]
//!   def menu_opens(t : T?) {
//!     send_action(t, "HUD.ToggleMenu")
//!     advance_frames(10)
//!     check_screenshot(t, "menu_open")    // compares with references/menu_open.png next to this file
//!   }

require danetlibs/test_harness/ecs_test public
require DagorConsole public
require DagorFiles
require DagorInput public
require DngTestMode

def send_action(t : T?; action_name : string) : bool {
  //! Triggers an input action as if its binding was pressed.
  let action = get_action_handle(action_name, uint16(0xFFFF))
  if (action == BAD_ACTION_HANDLE) {
    t |> failure("unknown input action '{action_name}'")
    return false
  }
  send_action_event(action)
  return true
}

def set_axis(t : T?; action_name : string; value : float) : bool {
  //! Sets an analog axis action (e.g. a trigger) until changed again.
  let action = get_action_handle(action_name, uint16(0xFFFF))
  if (action == BAD_ACTION_HANDLE) {
    t |> failure("unknown input action '{action_name}'")
    return false
  }
  return t |> success(set_analog_axis_action_state(action, value), "'{action_name}' is not an analog axis action")
}

def check_screenshot(t : T?; name : string; channel_tolerance : int = 8; max_rms : float = 1.0;
                     max_bad_pixels_percent : float = 0.5; max_frames : int = 300) : bool {
  //! Takes a screenshot (without UI) and compares it with references/<name>.png next to the test file
  //! (references/<name>.<3d driver>.png first). Mismatches write actual, reference and diff images to the report.
  //! A missing reference fails; rerun with test_all.py --update-references to create it.
  if (test_mode_is_dedicated()) {
    t |> failure("screenshots need a rendering game: use game:t=\"client\" in test.blk")
    return false
  }
  let file = test_mode_screenshot_path(name)
  dd_erase(file)
  console_command("screencap.take_screenshot_ext 0 -1 {name}")
  if (!advance_until(t, max_frames) <| $() { return dd_file_exists(file); }) {
    return false
  }
  let mismatch = test_mode_check_image(file, name, channel_tolerance, max_rms, max_bad_pixels_percent)
  return t |> success(empty(mismatch), mismatch)
}
