// The game's data files, checked without running the game: they parse, and the files they name exist

#include <unittest/dag_unitTest.h>
#include <ioSys/dag_dataBlock.h>
#include <osApiWrappers/dag_direct.h>

static String game_base(const char *rel) { return unittest::data_path(String(0, "../../gameBase/%s", rel)); }

TEST_CASE("settings.blk names the start scene and the entity templates", "[config]")
{
  DataBlock settings;
  REQUIRE(settings.load(game_base("config/settings.blk")));
  for (const char *key : {"scene", "entitiesPath"})
  {
    INFO(key);
    const char *path = settings.getStr(key, nullptr);
    REQUIRE(path != nullptr);
    CHECK(dd_file_exists(game_base(path)));
  }
}

TEST_CASE("the game data files parse", "[config]")
{
  for (const char *fn : {"config/gameparams.blk", "gamedata/templates/dng_empty.entities.blk", "gamedata/templates/weather.blk",
         "gamedata/templates/postfx.blk", "gamedata/scenes/main.blk", "gamedata/scenes/_common_render_scene.blk"})
  {
    INFO(fn);
    DataBlock blk;
    CHECK(blk.load(game_base(fn)));
  }
}
