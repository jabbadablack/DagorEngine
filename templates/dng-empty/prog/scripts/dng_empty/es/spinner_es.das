options gen2
require ecs
require dng_empty.spinner

// An entity system: every frame, entities with spinner__speed (radians per second) turn around their up axis
[es(tag=server, no_order)]
def spinner_es(info : UpdateStageInfoAct; spinner__speed : float; var transform : float3x4) {
  let angle = spinner__speed * info.dt
  transform[0] = rotate_around_up(transform[0], angle)
  transform[2] = rotate_around_up(transform[2], angle)
}
