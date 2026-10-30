options no_aot
options gen2
require ECSGlobalTags
require danetlibs.frame_graph_renderer.frame_graph_renderer_init

// Renderer lifecycle handlers must exist before the session creates entities.
[init]
def bootstrap {
    if (ecs_has_tag("render")) {
        let ok = load_frame_graph_renderer("%danetlibs/frame_graph_renderer")
        assert(ok)
    }
}
