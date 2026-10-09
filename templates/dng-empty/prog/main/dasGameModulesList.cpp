// das modules of the game itself: called by daNetGame's das init and by the AOT compiler

#include <daScript/misc/platform.h>
#include <daScript/daScriptModule.h>

das::Module *das_pull_RebuildNavMeshModule() { return nullptr; } // Note: dummy editor pathfinder's dep

void pull_game_das() {}
