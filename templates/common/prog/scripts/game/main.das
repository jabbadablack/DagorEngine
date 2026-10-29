options no_aot
options gen2
require ecs
require ecs.fs
require ECSGlobalTags
require danetlibs.frame_graph_renderer.frame_graph_renderer_init

[init]
def load {
    let ok = load_folder("%scripts/game/es")
    if (ecs_has_tag("render")) {
        load_frame_graph_renderer("%danetlibs/frame_graph_renderer")
    }
    assert(ok)
}
