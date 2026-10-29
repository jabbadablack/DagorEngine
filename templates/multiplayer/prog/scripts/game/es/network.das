require ecs

// Server-owned replicated gameplay state. Extend with validated input events.
[es(tag=server, no_order)]
def server_clock(info : UpdateStageInfoAct; var network__serverTime : float&)
  network__serverTime += info.dt
