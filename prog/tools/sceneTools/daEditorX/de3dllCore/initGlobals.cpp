// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <startup/dag_dllMain.inc.cpp>
#include <EditorCore/ec_IEditorCore.h>
#include <de3_interface.h>
#include <propPanel/propPanelService.h>
#include <de3_huid.h>
#include <oldEditor/de_interface.h>
#include <libTools/util/strUtil.h>
#include <drv/3d/dag_interface_table.h>
#include <math/dag_math3d.h>
#include <math/random/dag_random.h>
#include <imgui/imgui.h>
#include <EditorCore/ec_imguiTestHooks.h>
#include <stdarg.h>

IDagorEd2Engine *IDagorEd2Engine::__dagored_global_instance = NULL;
IDaEditor3Engine *IDaEditor3Engine::__daeditor3_global_instance = NULL;
IEditorCoreEngine *IEditorCoreEngine::__global_instance = nullptr;

IDagorRender *editorcore_extapi::dagRender = nullptr;
IDagorGeom *editorcore_extapi::dagGeom = nullptr;
IDagorConsole *editorcore_extapi::dagConsole = nullptr;
IDagorInput *editorcore_extapi::dagInput = nullptr;
IDagorTools *editorcore_extapi::dagTools = nullptr;
IDagorScene *editorcore_extapi::dagScene = nullptr;

D3dInterfaceTable d3di;
static SimpleString exePath;

void daeditor3_init_globals(IDagorEd2Engine &editor)
{
  IEditorCore &editor_core = *(IEditorCore *)editor.queryEditorInterfacePtr(HUID_IEditorCore);
  IDaEditor3Engine &editor3 = *(IDaEditor3Engine *)editor.queryEditorInterfacePtr(HUID_IDaEditor3Engine);
  G_ASSERT(&editor_core);
  G_ASSERT(&editor3);

  editorcore_extapi::dagRender = editor_core.getRender();
  G_ASSERT(editorcore_extapi::dagRender);
  editorcore_extapi::dagGeom = editor_core.getGeom();
  G_ASSERT(editorcore_extapi::dagGeom);
  editorcore_extapi::dagConsole = editor_core.getConsole();
  G_ASSERT(editorcore_extapi::dagConsole);
  editorcore_extapi::dagTools = editor_core.getTools();
  G_ASSERT(editorcore_extapi::dagTools);
  editorcore_extapi::dagInput = editor_core.getInput();
  G_ASSERT(editorcore_extapi::dagInput);
  editorcore_extapi::dagScene = editor_core.getScene();
  G_ASSERT(editorcore_extapi::dagScene);
  exePath = editor_core.getExePath();

  editorcore_extapi::dagRender->fillD3dInterfaceTable(d3di);

  // some of Dagor engine inits
  ::set_rnd_seed(editorcore_extapi::dagTools->refTimeUsec());
  ::init_math();

  IEditorCoreEngine::set(&editor);
  IDagorEd2Engine::set(&editor);
  IDaEditor3Engine::set(&editor3);

  if (PropPanel::IPropPanelService *svc = DAEDITOR3.getPropPanelService())
  {
    if (void *ctx = svc->getImguiContext())
    {
      ImGui::SetCurrentContext((ImGuiContext *)ctx);
    }
  }
}

String editorcore_extapi::make_full_start_path(const char *rel_path) { return ::make_full_path(exePath, rel_path); }

static const EditorImguiTestHooks *get_imgui_test_hooks()
{
  return DAGORED2 ? static_cast<const EditorImguiTestHooks *>(
    DAGORED2->queryEditorInterfacePtr(EditorImguiTestHooks::HUID)) : nullptr;
}
void ImGuiTestEngineHook_ItemAdd(ImGuiContext *ctx, unsigned id, const ImRect &bb, const ImGuiLastItemData *data)
{ if (auto *hooks=get_imgui_test_hooks()) hooks->itemAdd(ctx,id,bb,data); }
void ImGuiTestEngineHook_ItemInfo(ImGuiContext *ctx, unsigned id, const char *label, int flags)
{ if (auto *hooks=get_imgui_test_hooks()) hooks->itemInfo(ctx,id,label,flags); }
const char *ImGuiTestEngine_FindItemDebugLabel(ImGuiContext *ctx, unsigned id)
{ if (auto *hooks=get_imgui_test_hooks()) return hooks->debugLabel(ctx,id); return nullptr; }
void ImGuiTestEngineHook_Log(ImGuiContext *, const char *fmt, ...)
{
  va_list args; va_start(args,fmt); String message; message.cvprintf(0,fmt,args); va_end(args);
  debug("%s",message.c_str());
}
