options no_aot
options gen2
require ecs
require ecs.fs

[init]
def load {
    let ok = load_folder("%scripts/game/es")
    assert(ok)
}
