#default:forbid-root-table
// Quirrel is used for UI and editor integration. Gameplay belongs in daScript.
import "%dngscripts/ecs.nut" as ecs
import "app" as app
from "dagor.system" import get_arg_value_by_name, dgs_get_settings
from "dagor.workcycle" import defer, setTimeout
ecs.clear_vm_entity_systems()

// The host first opens the UI shell. Start the actual game/session once;
// source reloads must not restart an already running session.
function startWhenReady() {
if (!app.is_initial_loading_complete()) {
  setTimeout(0.05, startWhenReady)
  return
}
if (app.get_current_scene() == "") {
  let connect = get_arg_value_by_name("connect")
  if (connect != null && connect != "")
    app.launch_network_session({ host_urls = [connect] })
  else
    app.launch_network_session({
      scene = get_arg_value_by_name("scene") ?? dgs_get_settings()?["scene"] ?? "gamedata/scenes/starter.blk"
    })
}
}
defer(startWhenReady)
