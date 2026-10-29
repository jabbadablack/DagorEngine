require ecs
require math

// A complete example gameplay system: change rules here without a native rebuild.
[es(no_order)]
def starter_motion(info : UpdateStageInfoAct; var transform : float3x4;
                   var starter__elapsed : float&; starter__animate : bool = true)
  if !starter__animate
    return
  starter__elapsed += info.dt
  transform[3].y = 1.0 + 0.25 * sin(starter__elapsed)
