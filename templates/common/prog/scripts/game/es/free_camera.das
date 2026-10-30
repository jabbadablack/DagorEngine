require ecs
require starter_input
require gameLibs.render_events.render_events

// The engine flight integrator owns the camera. Input mapping is editable daScript.
[es(tag=render, before=free_cam_es)]
def starter_camera_input(info : UpdateStageInfoBeforeRender; camera__active : bool;
                         var free_cam__mouse, free_cam__move, free_cam__rotate : float2&;
                         var starter__cameraInputOwned : bool&;
                         var free_cam__shiftY : float&; var free_cam__turbo : bool&)
  if !camera__active || !camera_input_enabled()
    // Clear our contribution once, then let the editor drive its own camera.
    if starter__cameraInputOwned
      free_cam__move = float2(0)
      free_cam__rotate = float2(0)
      free_cam__mouse = float2(0)
      free_cam__shiftY = 0.0
      free_cam__turbo = false
      starter__cameraInputOwned = false
    return
  starter__cameraInputOwned = true
  free_cam__move = float2((key_down(32) ? 1.0 : 0.0) - (key_down(30) ? 1.0 : 0.0),
                          (key_down(17) ? 1.0 : 0.0) - (key_down(31) ? 1.0 : 0.0))
  free_cam__rotate = float2(0)
  free_cam__mouse += float2(mouse_dx(), mouse_dy())
  free_cam__shiftY = (key_down(18) ? 1.0 : 0.0) - (key_down(46) ? 1.0 : 0.0)
  free_cam__turbo = key_down(42)
