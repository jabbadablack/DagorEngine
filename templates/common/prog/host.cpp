// Project-specific daScript module registration hook required by daNetGame.
// Gameplay is implemented in prog/scripts/game; add native bindings here only as needed.
#include <daScript/daScript.h>
#include <drv/hid/dag_hiGlobals.h>
#include <drv/hid/dag_hiPointing.h>
#include <startup/dag_inpDevClsDrv.h>
#include <camera/sceneCam.h>

namespace
{
bool key_down(int code) { return code >= 0 && code < 256 && HumanInput::raw_state_kbd.isKeyDown(code); }
float mouse_dx() { return float(HumanInput::raw_state_pnt.mouse.deltaX); }
float mouse_dy() { return float(HumanInput::raw_state_pnt.mouse.deltaY); }
class StarterInput final : public das::Module
{
public:
  StarterInput() : das::Module("starter_input")
  {
    das::ModuleLibrary library(this);
    das::addExtern<DAS_BIND_FUN(key_down)>(*this, library, "key_down", das::SideEffects::accessExternal, "key_down");
    das::addExtern<DAS_BIND_FUN(mouse_dx)>(*this, library, "mouse_dx", das::SideEffects::accessExternal, "mouse_dx");
    das::addExtern<DAS_BIND_FUN(mouse_dy)>(*this, library, "mouse_dy", das::SideEffects::accessExternal, "mouse_dy");
  }
};
}
void pull_game_das()
{
  if (!das::Module::require("starter_input")) new StarterInput;
}

#include <startup/dag_globalSettings.h>
#include <util/dag_globDef.h>
#include <debug/dag_debug.h>
#include <main/gameLoad.h>
#include <daECS/core/entityManager.h>
#include <daECS/core/template.h>
#if DAGOR_DBGLEVEL > 0
#include <ecs/input/hidEventRouter.h>
#include <drv/hid/dag_hiKeybIds.h>
#include <drv/hid/dag_hiKeyboard.h>
#include <daEditorE/editorCommon/inGameEditor.h>
#include <util/dag_console.h>

namespace
{
bool tools_ready()
{
  return !sceneload::is_load_in_progress() && g_entity_mgr && g_entity_mgr->getTemplateDB().getTemplateByName("free_cam");
}
struct ToolKeys final : ecs::IGenHidEventHandler
{
  bool ehIsActive() const override { return true; }
  bool gmehMove(const Context &, float, float) override { return false; }
  bool gmehButtonDown(const Context &, int) override { return false; }
  bool gmehButtonUp(const Context &, int) override { return false; }
  bool gmehWheel(const Context &, int) override { return false; }
  bool gkehButtonDown(const Context &, int key, bool repeat, wchar_t) override
  {
    if (key != HumanInput::DKEY_F2 && key != HumanInput::DKEY_F10) return false;
    if (!tools_ready()) return true;
    if (!repeat) console::command(key == HumanInput::DKEY_F2 ? "daEd4.open" : "camera.free");
    return true;
  }
  bool gkehButtonUp(const Context &, int key) override
  {
    return key == HumanInput::DKEY_F2 || key == HumanInput::DKEY_F10;
  }
} toolKeys;
#if !STARTER_DEDICATED
bool smokeReady = false;
void template_smoke_test()
{
  if (!smokeReady || !tools_ready() || !dgs_get_argv("template-smoke-test")) return;
  static int frame = 0;
  ++frame;
  if (frame < 30 || frame % 5 != 0) return;
  auto *keyboard = global_cls_drv_kbd ? global_cls_drv_kbd->getDevice(0) : nullptr;
  auto *client = keyboard ? keyboard->getClient() : nullptr;
  if (!client) { logerr("template-smoke: no real keyboard event client"); quit_game(5); return; }
  auto press = [&](int key, bool repeat = false) {
    client->gkcButtonDown(keyboard, key, repeat, 0);
    if (!repeat) client->gkcButtonUp(keyboard, key);
  };
  auto require = [](bool condition, const char *message) {
    if (!condition) { logerr("template-smoke: %s", message); quit_game(5); }
    return condition;
  };
  switch (frame)
  {
    case 30: press(HumanInput::DKEY_F2); break;
    case 35:
      if (!require(is_editor_activated(), "F2 did not open the embedded editor")) return;
      press(HumanInput::DKEY_F2, true);
      if (!require(is_editor_activated(), "key repeat closed the editor")) return;
      press(HumanInput::DKEY_F2);
      break;
    case 40:
      if (!require(!is_editor_activated(), "F2 did not close the editor")) return;
      press(HumanInput::DKEY_F10);
      break;
    case 45:
      if (!require(is_free_camera_enabled(), "F10 did not enable free camera")) return;
      press(HumanInput::DKEY_F10, true);
      if (!require(is_free_camera_enabled(), "key repeat disabled free camera")) return;
      press(HumanInput::DKEY_F10);
      break;
    case 50:
      if (!require(!is_free_camera_enabled(), "F10 did not restore the game camera")) return;
      debug("template-smoke: keyboard event routing, daRg editor and free camera passed");
      quit_game(0);
      break;
  }
}
#endif
}
#endif

namespace gameproj
{
void before_init_video() {}
void init_before_main_loop()
{
#if DAGOR_DBGLEVEL > 0
  // Run before other development overlays can consume F2. UI remains Quirrel/daRg.
  register_hid_event_handler(&toolKeys, 1000);
#if !STARTER_DEDICATED
  smokeReady = true;
#endif
#endif
}
void update_before_dagor_work_cycle()
{
#if !STARTER_DEDICATED
#if DAGOR_DBGLEVEL > 0
  static bool initialModeApplied = false;
  if (!initialModeApplied && tools_ready())
  {
    initialModeApplied = true;
    if (dgs_get_argv("editor") || dgs_get_argv("edit")) console::command("daEd4.open 1");
    if (dgs_get_argv("freecam")) console::command("camera.free 1");
  }
  template_smoke_test();
#endif
  if (global_cls_drv_pnt)
    if (auto *mouse = global_cls_drv_pnt->getDevice(0))
      mouse->setRelativeMovementMode(is_free_camera_enabled());
#endif
}
void post_shutdown_handler()
{
#if DAGOR_DBGLEVEL > 0
  unregister_hid_event_handler(&toolKeys);
#endif
}
void reset_game_resources() {}
}
