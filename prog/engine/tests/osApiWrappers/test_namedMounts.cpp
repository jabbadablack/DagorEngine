// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include <osApiWrappers/dag_basePath.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>
#include <stdlib.h>
#if _TARGET_PC_WIN
#include <direct.h>
#define chdir  _chdir
#define getcwd _getcwd
#else
#include <unistd.h>
#endif

static void write_text(const char *fn, const char *text)
{
  REQUIRE(dd_mkpath(fn));
  file_ptr_t f = df_open(fn, DF_WRITE | DF_CREATE);
  REQUIRE(f);
  df_write(f, text, (int)strlen(text));
  df_close(f);
}

TEST_CASE("named mounts resolve other mounts in their path", "[namedMounts]")
{
  dd_set_named_mount_path("testBase", "/data/base");
  dd_set_named_mount_path("testChained", "%testBase/sub/dir/");
  CHECK(String(dd_get_named_mount_path("testChained")) == "/data/base/sub/dir");

  String resolved;
  REQUIRE(dd_resolve_named_mount(resolved, "%testChained/file.txt"));
  CHECK(resolved == "/data/base/sub/dir/file.txt");

  dd_set_named_mount_path("testBase", "/elsewhere"); // stored resolved: later changes of the base don't propagate
  CHECK(String(dd_get_named_mount_path("testChained")) == "/data/base/sub/dir");
  dd_set_named_mount_path("testChained", nullptr);
  dd_set_named_mount_path("testBase", nullptr);
  CHECK(dd_get_named_mount_path("testChained") == nullptr);
}

// %engine is detected once per process, so this is the only case that may trigger the detection
TEST_CASE("the engine mount is found through a project's engine.blk", "[namedMounts]")
{
  if (getenv("DAGOR_ENGINE_ROOT"))
    SKIP("DAGOR_ENGINE_ROOT is set: it takes precedence over engine.blk");

  const String scratch = unittest::scratch_dir();
  write_text(String(0, "%s/MyGame/engine.blk", scratch.c_str()), "engineRoot:t=\"../TheEngine\"\n");
  REQUIRE(dd_mkdir(String(0, "%s/MyGame/game/content", scratch.c_str())));

  char savedCwd[DAGOR_MAX_PATH];
  REQUIRE(getcwd(savedCwd, sizeof(savedCwd)));
  REQUIRE(chdir(String(0, "%s/MyGame/game/content", scratch.c_str())) == 0); // games and tools run below the project root
  dd_set_named_mount_path("engine", nullptr);
  const char *engine = dd_get_named_mount_path("engine");
  REQUIRE(chdir(savedCwd) == 0);

  REQUIRE(engine != nullptr);
  String expected(0, "%s/TheEngine", scratch.c_str());
  dd_simplify_fname_c(expected.data());
  expected.updateSz();
  CHECK(String(engine) == expected);

  dd_set_named_mount_path("gameLibs", "%engine/prog/gameLibs"); // what project settings.blk files do
  String libs;
  REQUIRE(dd_resolve_named_mount(libs, "%gameLibs/x.das"));
  CHECK(libs == String(0, "%s/prog/gameLibs/x.das", expected.c_str()));
  dd_set_named_mount_path("gameLibs", nullptr);
}

TEST_CASE("an explicitly set engine mount wins", "[namedMounts]")
{
  dd_set_named_mount_path("engine", "/explicit/engine");
  CHECK(String(dd_get_named_mount_path("engine")) == "/explicit/engine");
  dd_set_named_mount_path("engine", nullptr);
}
