// Project-specific daScript module registration hook required by daNetGame.
// Gameplay is implemented in prog/scripts/game; add native bindings here only as needed.
#include <daScript/daScript.h>
#include <drv/hid/dag_hiGlobals.h>
#include <drv/hid/dag_hiPointing.h>
#include <startup/dag_inpDevClsDrv.h>
#include <camera/sceneCam.h>
#include <atomic>
#if DAGOR_DBGLEVEL > 0
#include <daEditorE/editorCommon/inGameEditor.h>
#endif

namespace
{
bool key_down(int code) { return code >= 0 && code < 256 && HumanInput::raw_state_kbd.isKeyDown(code); }
std::atomic<float> pendingMouseX{0}, pendingMouseY{0};
float mouse_dx() { return pendingMouseX.exchange(0, std::memory_order_relaxed); }
float mouse_dy() { return pendingMouseY.exchange(0, std::memory_order_relaxed); }
bool camera_input_enabled()
{
#if DAGOR_DBGLEVEL > 0 && !STARTER_DEDICATED
  return is_free_camera_enabled() && (!is_editor_activated() || is_editor_free_camera_enabled());
#else
  return false;
#endif
}
void accumulate_mouse_motion(float dx, float dy)
{
  if (camera_input_enabled())
  {
    pendingMouseX.fetch_add(dx, std::memory_order_relaxed);
    pendingMouseY.fetch_add(dy, std::memory_order_relaxed);
  }
}
class StarterInput final : public das::Module
{
public:
  StarterInput() : das::Module("starter_input")
  {
    das::ModuleLibrary library(this);
    das::addExtern<DAS_BIND_FUN(key_down)>(*this, library, "key_down", das::SideEffects::accessExternal, "key_down");
    das::addExtern<DAS_BIND_FUN(mouse_dx)>(*this, library, "mouse_dx", das::SideEffects::modifyExternal, "mouse_dx");
    das::addExtern<DAS_BIND_FUN(mouse_dy)>(*this, library, "mouse_dy", das::SideEffects::modifyExternal, "mouse_dy");
    das::addExtern<DAS_BIND_FUN(camera_input_enabled)>(*this, library, "camera_input_enabled", das::SideEffects::accessExternal, "camera_input_enabled");
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
#include <util/dag_console.h>
#include <render/renderer.h>

namespace
{
bool tools_ready()
{
  return !sceneload::is_load_in_progress() && g_entity_mgr && g_entity_mgr->getTemplateDB().getTemplateByName("free_cam");
}
struct ToolKeys final : ecs::IGenHidEventHandler
{
  bool ehIsActive() const override { return true; }
  bool gmehMove(const Context &, float dx, float dy) override
  {
    // Keep the deterministic test independent of desktop mouse activity.
    if (!dgs_get_argv("template-smoke-test")) accumulate_mouse_motion(dx, dy);
    return false; // The editor and UI still receive pointer events.
  }
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
  auto *mouse = global_cls_drv_pnt ? global_cls_drv_pnt->getDevice(0) : nullptr;
  if (!client) { logerr("template-smoke: no real keyboard event client"); quit_game(5); return; }
  if (!mouse) { logerr("template-smoke: no real pointer device"); quit_game(5); return; }
  static Point3 directionBeforeInput, settledDirection;
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
    case 30:
      if (!require(get_world_renderer() != nullptr, "the starter world renderer was not created")) return;
      press(HumanInput::DKEY_F2);
      break;
    case 35:
      if (!require(is_editor_activated(), "F2 did not open the embedded editor")) return;
      if (!require(!mouse->getRelativeMovementMode(), "editor cursor remained captured")) return;
      accumulate_mouse_motion(12, -7);
      if (!require(mouse_dx() == 0 && mouse_dy() == 0, "editor pointer motion leaked into fly camera")) return;
      press(HumanInput::DKEY_F2, true);
      if (!require(is_editor_activated(), "key repeat closed the editor")) return;
      break;
    case 40:
      if (!require(!mouse->getRelativeMovementMode(), "editor cursor capture changed unexpectedly")) return;
      press(HumanInput::DKEY_F2);
      break;
    case 45:
      if (!require(!is_editor_activated(), "F2 did not close the editor")) return;
      press(HumanInput::DKEY_F10);
      break;
    case 50:
      if (!require(is_free_camera_enabled(), "F10 did not enable free camera")) return;
      if (!require(mouse->getRelativeMovementMode(), "game fly camera did not capture the mouse")) return;
      press(HumanInput::DKEY_F10, true);
      if (!require(is_free_camera_enabled(), "key repeat disabled free camera")) return;
      pendingMouseX.store(0, std::memory_order_relaxed);
      pendingMouseY.store(0, std::memory_order_relaxed);
      accumulate_mouse_motion(12, -7);
      if (!require(mouse_dx() == 12 && mouse_dy() == -7 && mouse_dx() == 0 && mouse_dy() == 0,
          "mouse movement was replayed instead of consumed")) return;
      directionBeforeInput = get_cam_itm().getcol(2);
      accumulate_mouse_motion(0, 32);
      break;
    case 55:
      if (!require(fabsf(get_cam_itm().getcol(2).y - directionBeforeInput.y) > 0.00001f &&
          fabsf(get_cam_itm().getcol(2).x - directionBeforeInput.x) < 0.00001f, "vertical mouse input did not produce pitch only")) return;
      break;
    case 60: settledDirection = get_cam_itm().getcol(2); break;
    case 65:
      if (!require(lengthSq(get_cam_itm().getcol(2) - settledDirection) < 1e-9f, "camera kept rotating without mouse movement")) return;
      directionBeforeInput = get_cam_itm().getcol(2);
      accumulate_mouse_motion(32, 0);
      break;
    case 70:
      if (!require(fabsf(get_cam_itm().getcol(2).x - directionBeforeInput.x) > 0.00001f &&
          fabsf(get_cam_itm().getcol(2).y - directionBeforeInput.y) < 0.00001f, "horizontal mouse input did not produce yaw only")) return;
      break;
    case 75: settledDirection = get_cam_itm().getcol(2); break;
    case 80:
      if (!require(lengthSq(get_cam_itm().getcol(2) - settledDirection) < 1e-9f, "camera yaw did not settle after input stopped")) return;
      press(HumanInput::DKEY_F10);
      break;
    case 85:
      if (!require(!is_free_camera_enabled(), "F10 did not restore the game camera")) return;
      debug("template-smoke: editor cursor, fly capture, one-shot mouse input, pitch/yaw and idle stability passed");
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
  // uishared::update owns mouse capture for gameplay, editor and UI modes.
  static bool hadCameraInput = false;
  const bool hasCameraInput = camera_input_enabled();
  if (hasCameraInput != hadCameraInput)
  {
    pendingMouseX.store(0, std::memory_order_relaxed);
    pendingMouseY.store(0, std::memory_order_relaxed);
    hadCameraInput = hasCameraInput;
  }
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
