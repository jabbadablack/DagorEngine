#include "editor.h"
#include "multiplayer.h"
#include <chrono>
#include <startup/dag_globalSettings.h>
#include <startup/dag_loadSettings.h>
#include <startup/dag_restart.h>
#include <workCycle/dag_gameScene.h>
#include <workCycle/dag_startupModules.h>
#include <workCycle/dag_workCycle.h>
#include <drv/3d/dag_renderTarget.h>
#include <drv/3d/dag_consts.h>
#include <perfMon/dag_cpuFreq.h>
#include <osApiWrappers/dag_cpuJobs.h>
#include <util/dag_globDef.h>

#define __DAGOR_OVERRIDE_DEFAULT_ROOT_RELATIVE_PATH ".."
#if _TARGET_PC_WIN
#include <startup/dag_winMain.inc.cpp>
#elif _TARGET_PC_LINUX
#include <startup/dag_linuxMain.inc.cpp>
#endif

class GameScene final : public DagorGameScene
{
public:
  void actScene() override
  {
    multiplayer::update();
    starter_editor::update(dagor_game_act_time);
  }
  void drawScene() override
  {
    // Add your game rendering here, then draw the shared editor viewport.
    d3d::clearview(CLEAR_TARGET, (multiplayer::connected() ? E3DCOLOR(24, 96, 48, 255) : E3DCOLOR(24, 40, 64, 255)), 1.0f, 0);
    starter_editor::render();
  }
};

void DagorWinMainInit(int, bool) {}
static void shutdown_game_project()
{
  multiplayer::shutdown();
  starter_editor::shutdown();
  dagor_select_game_scene(nullptr);
  shutdown_game(RESTART_ALL);
  cpujobs::term(true);
}
int DagorWinMain(int nCmdShow, bool)
{
  measure_cpu_freq();
  cpujobs::init();
  dgs_load_settings_blk(true, "settings.blk");
  dgs_post_shutdown_handler = shutdown_game_project;
  if (!multiplayer::initialize()) quit_game(1);
  dagor_init_video("@GAME_NAME@Window", nCmdShow, nullptr, "@GAME_NAME@");
  dagor_init_keyboard_win();
  dagor_init_mouse_win();
  dagor_common_startup();
  starter_editor::initialize();
  if (dgs_get_argv("editor-smoke-test") && !starter_editor::self_test()) quit_game(3);
  static GameScene scene;
  dagor_select_game_scene(&scene);
  dagor_reset_spent_work_time();
  const bool smokeTest = dgs_get_argv("smoke-test") != nullptr;
  const auto deadline = std::chrono::steady_clock::now() + std::chrono::seconds(15);
  for (;;)
  {
    dagor_work_cycle();
    if (smokeTest && std::chrono::steady_clock::now() > deadline) quit_game(2);
    if (smokeTest && multiplayer::connected())
      quit_game(0);
  }
}
