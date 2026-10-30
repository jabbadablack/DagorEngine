options no_aot
options gen2
require ecs
require ecs.fs
require ECSGlobalTags

[init]
def load {
    // CDK tools share rendering scripts but do not link this game's native input module.
    if (ecs_has_tag("inside_tools")) {
        return
    }
    let ok = load_folder("%scripts/game/es")
    assert(ok)
}
