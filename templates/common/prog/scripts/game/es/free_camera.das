require ecs
require starter_input

// The engine flight integrator owns the camera. Input mapping is editable daScript.
[es(tag=render, no_order)]
def starter_camera_input(info : UpdateStageInfoAct; camera__active : bool;
                         var free_cam__move, free_cam__rotate : float2&;
                         var free_cam__shiftY : float&; var free_cam__turbo : bool&)
  if !camera__active
    free_cam__move = float2(0)
    free_cam__rotate = float2(0)
    free_cam__shiftY = 0.0
    free_cam__turbo = false
    return
  free_cam__move = float2((key_down(32) ? 1.0 : 0.0) - (key_down(30) ? 1.0 : 0.0),
                          (key_down(17) ? 1.0 : 0.0) - (key_down(31) ? 1.0 : 0.0))
  free_cam__rotate = float2(mouse_dx(), -mouse_dy())
  free_cam__shiftY = (key_down(18) ? 1.0 : 0.0) - (key_down(46) ? 1.0 : 0.0)
  free_cam__turbo = key_down(42)
