#include "editor.h"
#include "engine_paths.h"
#include <util/dag_flyMode.h>
#include <util/dag_globDef.h>
#include <math/dag_TMatrix.h>
#include <math/dag_bounds3.h>
#include <debug/dag_debug.h>
#include <debug/dag_debug3d.h>
#include <drv/3d/dag_matricesAndPerspective.h>
#include <drv/3d/dag_renderTarget.h>
#include <drv/hid/dag_hiGlobals.h>
#include <drv/hid/dag_hiKeybIds.h>
#include <drv/hid/dag_hiPointing.h>
#include <startup/dag_inpDevClsDrv.h>
#include <startup/dag_globalSettings.h>
#include <startup/dag_restart.h>
#include <shaders/dag_shaders.h>
#include <gui/dag_imgui.h>
#include <imgui/imgui.h>
#include <imgui/imguiInput.h>
#include <ecs/input/hidEventRouter.h>
#include <ioSys/dag_dataBlock.h>
#include <osApiWrappers/dag_direct.h>
#include <vector>
#include <cstdio>
#include <cmath>

namespace starter_editor
{
struct Object
{
  char name[64] = "Cube";
  Point3 position = Point3(0, 1, 0);
  Point3 extent = Point3(1, 1, 1);
};
static std::vector<Object> objects;
static FlyModeBlackBox *camera = nullptr;
static TMatrix gameCamera = TMatrix::IDENT;
static bool editorActive = false, freeCamera = false, wasFreeCamera = false, dirty = false;
static int selected = 0;
static const char *status = "F2: editor | F10: free camera";

static void stop_camera()
{
  TMatrix pose;
  camera->getInvViewMatrix(pose);
  camera->resetDynamic();
  camera->setViewMatrix(pose);
  HumanInput::raw_state_pnt.resetDelta();
}

static void set_editor(bool active)
{
  if (active == editorActive) return;
  stop_camera();
  if (active)
  {
    wasFreeCamera = freeCamera;
    editorActive = true;
    imgui_request_state_change(ImGuiState::ACTIVE);
  }
  else
  {
    editorActive = false;
    freeCamera = wasFreeCamera;
    imgui_request_state_change(ImGuiState::OFF);
  }
  debug("starter editor: %s", active ? "active" : "game");
}

static struct ModeKeys final : ecs::IGenHidEventHandler
{
  bool ehIsActive() const override { return true; }
  bool gmehMove(const Context &, float, float) override { return false; }
  bool gmehButtonDown(const Context &, int) override { return false; }
  bool gmehButtonUp(const Context &, int) override { return false; }
  bool gmehWheel(const Context &, int) override { return false; }
  bool gkehButtonUp(const Context &, int) override { return false; }
  bool gkehButtonDown(const Context &, int key, bool repeat, wchar_t) override
  {
    if (key == HumanInput::DKEY_F2 || key == HumanInput::DKEY_F10)
    {
      if (!repeat)
      {
        if (key == HumanInput::DKEY_F2) set_editor(!editorActive);
        else
        {
          if (editorActive) { set_editor(false); freeCamera = true; }
          else freeCamera = !freeCamera;
          stop_camera();
        }
      }
      return true;
    }
    if (key == HumanInput::DKEY_ESCAPE && !ImGui::GetIO().WantTextInput)
      quit_game(0);
    return false;
  }
} modeKeys;

static bool finite(const Point3 &p)
{
  return std::isfinite(p.x) && std::isfinite(p.y) && std::isfinite(p.z);
}

static bool save_scene(const char *file)
{
  DataBlock scene;
  for (const Object &object : objects)
  {
    DataBlock *block = scene.addNewBlock("object");
    block->setStr("name", object.name);
    block->setPoint3("position", object.position);
    block->setPoint3("extent", object.extent);
  }
  dd_mkdir("scenes");
  if (!scene.saveToTextFile(file)) { status = "Could not save scene"; return false; }
  dirty = false;
  status = "Scene saved";
  return true;
}

static bool load_scene(const char *file)
{
  DataBlock scene;
  if (!scene.load(file) || scene.blockCount() > 256) { status = "Could not load scene"; return false; }
  std::vector<Object> loaded;
  for (int i = 0; i < scene.blockCount(); ++i)
  {
    const DataBlock *block = scene.getBlock(i);
    Object object;
    snprintf(object.name, sizeof(object.name), "%s", block->getStr("name", "Cube"));
    object.position = block->getPoint3("position", Point3(0, 1, 0));
    object.extent = block->getPoint3("extent", Point3(1, 1, 1));
    if (!finite(object.position) || !finite(object.extent) || object.extent.x <= 0 || object.extent.y <= 0 || object.extent.z <= 0)
      { status = "Scene contains an invalid transform"; return false; }
    loaded.push_back(object);
  }
  objects.swap(loaded);
  selected = objects.empty() ? -1 : 0;
  dirty = false;
  status = "Scene loaded";
  return true;
}

void initialize()
{
  camera = create_flymode_bb();
  gameCamera.setcol(3, Point3(0, 3, -10));
  camera->setViewMatrix(gameCamera);
  for (int i = 0; i < 3; ++i)
  {
    Object object;
    snprintf(object.name, sizeof(object.name), "Cube %d", i + 1);
    object.position.x = float(i - 1) * 3.0f;
    objects.push_back(object);
  }
  const char *shaderPrefix = dgs_get_settings()->getStr("editorShaderPrefix", DAGOR_EDITOR_SHADER_PREFIX);
  startup_shaders(shaderPrefix);
  startup_game(RESTART_ALL);
  DataBlock options;
  options.setBool("imgui_multiview", false);
  imgui_set_override_blk(options);
  imgui_init_on_demand();
  imgui_use_hybrid_input_mode(true);
  // Register the engine input adapter once; subsequent mode changes request an
  // explicit state so two toggles before a render cannot desynchronize the UI.
  imgui_switch_state();
  imgui_request_state_change(ImGuiState::OFF);
  register_hid_event_handler(&modeKeys, 400);
  freeCamera = dgs_get_argv("freecam") != nullptr;
  if (dgs_get_argv("editor") || dgs_get_argv("edit")) set_editor(true);
  if (dd_file_exist("scenes/starter_scene.blk")) load_scene("scenes/starter_scene.blk");
}

void update(float dt)
{
  const auto &kbd = HumanInput::raw_state_kbd;
  auto &mouse = HumanInput::raw_state_pnt;
  const bool canMove = !ImGui::GetIO().WantTextInput &&
    ((editorActive && mouse.mouse.isBtnDown(1) && !imgui_want_capture_mouse()) || (!editorActive && freeCamera));
  if (canMove)
  {
    camera->keys.fwd = kbd.isKeyDown(HumanInput::DKEY_W);
    camera->keys.back = kbd.isKeyDown(HumanInput::DKEY_S);
    camera->keys.left = kbd.isKeyDown(HumanInput::DKEY_A);
    camera->keys.right = kbd.isKeyDown(HumanInput::DKEY_D);
    camera->keys.worldUp = kbd.isKeyDown(HumanInput::DKEY_E);
    camera->keys.worldDown = kbd.isKeyDown(HumanInput::DKEY_C);
    camera->keys.turbo = kbd.isKeyDown(HumanInput::DKEY_LSHIFT);
    camera->integrate(dt, mouse.mouse.deltaX, mouse.mouse.deltaY);
    mouse.resetDelta();
  }
  else stop_camera();
  if (global_cls_drv_pnt)
    if (auto *device = global_cls_drv_pnt->getDevice(0)) device->setRelativeMovementMode(canMove);
}

void render()
{
  TMatrix pose = gameCamera;
  if (freeCamera || editorActive) camera->getInvViewMatrix(pose);
  d3d::settm(TM_VIEW, inverse(pose));
  d3d::settm(TM_WORLD, TMatrix::IDENT);
  int w = 1280, h = 720;
  d3d::get_screen_size(w, h);
  d3d::setpersp(Driver3dPerspective(1.3f, 1.3f * float(w) / float(h ? h : 1), 0.1f, 1000, 0, 0));
  begin_draw_cached_debug_lines(false, false);
  for (int i = -20; i <= 20; ++i)
  {
    draw_cached_debug_line(Point3(float(i), 0, -20), Point3(float(i), 0, 20), E3DCOLOR(70, 70, 80));
    draw_cached_debug_line(Point3(-20, 0, float(i)), Point3(20, 0, float(i)), E3DCOLOR(70, 70, 80));
  }
  for (size_t i = 0; i < objects.size(); ++i)
  {
    const Object &object = objects[i];
    draw_cached_debug_box(BBox3(object.position - object.extent, object.position + object.extent),
      editorActive && int(i) == selected ? E3DCOLOR(255, 210, 40) : E3DCOLOR(170, 195, 220));
  }
  end_draw_cached_debug_lines();
  imgui_update(w, h);
  if (editorActive)
  {
    ImGui::SetNextWindowSize(ImVec2(360, 460), ImGuiCond_FirstUseEver);
    if (ImGui::Begin("Scene editor"))
    {
      ImGui::TextUnformatted("F2: game/editor | F10: free camera");
      ImGui::TextUnformatted("RMB + WASD/E/C: fly | Shift: faster");
      if (ImGui::Button("Save scene")) save_scene("scenes/starter_scene.blk");
      ImGui::SameLine();
      if (ImGui::Button("Load scene")) load_scene("scenes/starter_scene.blk");
      ImGui::Text("%s%s", status, dirty ? " (modified)" : "");
      if (objects.size() < 256 && ImGui::Button("Add cube"))
      {
        objects.push_back(Object{}); selected = int(objects.size()) - 1; dirty = true;
      }
      ImGui::Separator();
      for (size_t i = 0; i < objects.size(); ++i)
      {
        ImGui::PushID(int(i));
        if (ImGui::Selectable(objects[i].name, int(i) == selected)) selected = int(i);
        ImGui::PopID();
      }
      if (selected >= 0 && selected < int(objects.size()))
      {
        Object &object = objects[selected];
        dirty |= ImGui::InputText("Name", object.name, sizeof(object.name));
        dirty |= ImGui::DragFloat3("Position", &object.position.x, 0.1f);
        dirty |= ImGui::DragFloat3("Half size", &object.extent.x, 0.05f, 0.05f, 100.0f);
        if (!finite(object.position)) object.position = Point3(0, 1, 0);
        if (!finite(object.extent)) object.extent = Point3(1, 1, 1);
        object.extent.x = object.extent.x < 0.05f ? 0.05f : object.extent.x;
        object.extent.y = object.extent.y < 0.05f ? 0.05f : object.extent.y;
        object.extent.z = object.extent.z < 0.05f ? 0.05f : object.extent.z;
        if (ImGui::Button("Delete selected"))
        {
          objects.erase(objects.begin() + selected);
          selected = objects.empty() ? -1 : 0;
          dirty = true;
        }
      }
    }
    ImGui::End();
    imgui_render();
  }
  else imgui_endframe();
}

bool self_test()
{
  const bool initialEditor = editorActive, initialFree = freeCamera;
  if (editorActive) set_editor(false);
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F10, false, 0);
  if (freeCamera == initialFree) return false;
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F10, true, 0);
  if (freeCamera == initialFree) return false;
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F10, false, 0);
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F2, false, 0);
  if (!editorActive) return false;
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F2, true, 0);
  if (!editorActive) return false;
  modeKeys.gkehButtonDown({}, HumanInput::DKEY_F2, false, 0);
  if (editorActive) return false;
  set_editor(initialEditor);
  TMatrix before, after;
  camera->getInvViewMatrix(before);
  camera->keys.fwd = 1;
  camera->integrate(1.0f, 0, 0);
  camera->getInvViewMatrix(after);
  if (after.getcol(3).z <= before.getcol(3).z) return false;
  stop_camera();
  camera->integrate(1.0f, 0, 0);
  TMatrix stopped;
  camera->getInvViewMatrix(stopped);
  if (lengthSq(stopped.getcol(3) - after.getcol(3)) > 0.0001f) return false;
  const Point3 original = objects[0].position;
  if (!save_scene("scenes/.editor-smoke.blk")) return false;
  objects[0].position.x += 12;
  if (!load_scene("scenes/.editor-smoke.blk") || objects[0].position != original) return false;
  dd_erase("scenes/.editor-smoke.blk");
  camera->setViewMatrix(gameCamera);
  debug("editor-smoke: modes, camera movement/release and scene persistence passed");
  return true;
}

void shutdown()
{
  unregister_hid_event_handler(&modeKeys);
  imgui_request_state_change(ImGuiState::OFF);
  imgui_update();
  imgui_shutdown();
  close_draw_cached_debug();
  delete camera;
  camera = nullptr;
  objects.clear();
}
}
