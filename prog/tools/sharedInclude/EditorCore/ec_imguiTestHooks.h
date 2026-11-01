// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
struct ImGuiContext;
struct ImGuiLastItemData;
struct ImRect;

// Optional query interface: DLL widgets submit to the host's single test item
// tree instead of linking a second, unadvanced copy of the test runtime.
struct EditorImguiTestHooks
{
  static constexpr unsigned HUID = 0x43534754;
  void (*itemAdd)(ImGuiContext *, unsigned, const ImRect &, const ImGuiLastItemData *);
  void (*itemInfo)(ImGuiContext *, unsigned, const char *, int);
  const char *(*debugLabel)(ImGuiContext *, unsigned);
};
