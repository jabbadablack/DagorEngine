# In-Game Tests (ECS and Scenarios)

daNetGame based games have a *test mode*: started with `-das_test:<path>`, the game loads normally, then loads the
test files like any other game script, runs every `[ecs_test]` function and exits with the
[test exit code](overview.md#results). Tests see the whole game: every das module, ECS system, template and the loaded
scene. Two layers use it:

- `ecs`: the headless dedicated server; fast, for gameplay logic over entities and frames.
- `scenario`: the rendering client; for end-to-end behavior, input and screenshots.

## Writing tests

```text
options gen2
require ecs
require danetlibs/test_harness/ecs_test

[ecs_test]
def projectile_hits_target(t : T?) {
  let target = createEntitySync("dummy_target")
  createEntitySync("test_projectile") <| $(var init) {
    set(init, "transform", ...)
  }
  t |> success(advance_until(t, 120) <| $() { return get_bool(target, "hit") ?? false; })
  t |> expect_logerr("target destroyed without owner", 1) <| $() {
    destroyEntity(target)
    advance_frames(1)
  }
}
```

- `[ecs_test] def name(t : T?)` declares a test; the body uses dastest's `T` API (see
  [daScript unit tests](das_unit_tests.md)), sub tests (`t |> run(...)`) are reported as `name/sub`.
- `advance_frames(n)` runs n complete game frames (act, ECS updates, rendering on the client), each advancing the game by
  `test_mode_fixed_dt()` seconds (1/60 unless `-test_dt` is passed), as fast as the machine allows.
- `advance_until(t, max_frames) <| $() { return condition; }` runs frames until the condition holds, failing the test
  otherwise.
- `expect_logerr(t, substring, count) <| $() { ... }` declares errors the block provokes on purpose. Any other error
  fails the running test, including errors logged during game startup (reported as `<game startup>`).
- Test files may declare their own entity systems (`[es]`) and use queries like any game script; they are loaded only
  in test mode, never shipped.

### Scenarios

`require danetlibs/test_harness/scenario` adds what a player does and sees:

```text
[ecs_test]
def pause_menu_opens(t : T?) {
  send_action(t, "HUD.Pause")           // an input action, as if its binding was pressed
  advance_frames(10)
  check_screenshot(t, "pause_menu")     // compares with references/pause_menu.png next to this file
}
```

`set_axis(t, action, value)` drives analog actions; `console_command("...")` runs console commands. Physical
keyboards, mice and gamepads are disabled in scenario runs, so the person at the machine can't affect results.
`check_screenshot` takes a screenshot without UI, waits for it and compares it with `references/<name>.png`
(`references/<name>.<3d driver>.png` first). The tolerances are parameters: `channel_tolerance` (default 8),
`max_rms` (1.0) and `max_bad_pixels_percent` (0.5). Create or update references with
`python test_all.py run --update-references` and review the images before committing them.

## Project setup

The game needs to find dastest and the test harness:

- a mount point for dastest in `settings.blk`:
  `"%dastest" { forSource:t="<engine>/prog/1stPartyLibs/daScript/dastest"; forVromfs:t="dastest"; }`
- two entries in the game's `.das_project`: `"dastest" => "%dastest"` in the module prefixes and
  `"testing" => "%dastest/testing.das"` in the aliases (dastest's own modules require each other by those names).

Tests run from sources (the runner passes `-config:debug/useAddonVromSrc:b=yes`), so neither the tests nor the
`test_harness` lib need to be in the game's vromfs. The project's root `test.blk` names the game:

```text
game{
  codename:t="my_game"                 // executable base name (my_game-dev, my_game-ded-dev)
  dir:t="game"                         // runtime dir with <platform>-<arch>/ executables
  build:t="{python} project.py build code" // optional: run once from the project root before in-game targets
}
```

and targets point at test files:

```text
target{ name:t="myGame.ecs"; layer:t="ecs"; path:t="tests/ecs"; scene:t="gamedata/scenes/test.blk"; caseTimeout:r=60 }
target{ name:t="myGame.scenarios"; layer:t="scenario"; path:t="tests/scenarios"; scene:t="gamedata/scenes/test.blk" }
```

`game:t="client"` runs `ecs` tests in the client, `game:t="dedicated"` runs scenarios headless (screenshots then fail).
Scenario targets require a GPU and a display and never run in parallel with other GPU targets.

## Running the game in test mode by hand

```bash
cd game
windows-x86_64/my_game-ded-dev.exe -das_test:../prog/tests/ecs -test_out:../_test_out -scene:gamedata/scenes/test.blk \
  -nolisten -stdout -config:debug/useAddonVromSrc:b=yes
```

| Option | Meaning |
|---|---|
| `-das_test:<path>` | test file or directory (recursive); repeatable; named mounts allowed |
| `-test_filter:<prefix>` | only tests whose name starts with the prefix; repeatable |
| `-test_out:<dir>` | where `dastest.json` (results) and `events.jsonl` are written |
| `-test_timeout:<sec>` | per test limit (default 300): the game exits with code 3 when exceeded |
| `-test_dt:<sec>` | game time per frame (default 1/60) |
| `-test_update_references` | image checks write missing or mismatching references |
