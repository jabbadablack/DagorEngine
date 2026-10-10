# Dng Empty

A daNetGame game built with the Dagor Engine. `engine.blk` names the engine checkout (relative to this dir or
absolute); the project can be anywhere.

## Build and run

```bash
python project.py build              # everything: code, shaders, vromfs, tools (editor snapshot), assets
python project.py build code         # some of them: just the client and the dedicated server
game/client.cmd                      # or game/client.sh: runs the game on the scripts and data in prog/
game/server.cmd                      # the dedicated server; clients join with client.cmd -connect:localhost
```

The engine's tools have to be built first (`python dng.py build cdk` in the engine): the shader
compilers, vromfsPacker and dabuild find the engine through `engine.blk` too.

## Layout

```text
engine.blk          the engine checkout this project is built with
project.py          setup, relink, build, test, info (python project.py -h)
application.blk     the tools' setup (daEditor, daViewer, dabuild, impostorBaker)
develop/            tool scripts (daEditor, daViewer, dabuild, daImpostor), assets/ and levels/
game/               what ships: executables, compiledShaders, vromfs, content (all built), run scripts
prog/
  jamfile           the game executables (jam; -sDedicated=yes for the server)
  build.py          the build steps of python project.py build
  danetgamelibs.txt engine libs the game uses (prog/daNetGameLibs), gamelibs.txt likewise for prog/gameLibs
  prog.vromfs.blk   what goes into game/dng_empty.vromfs.bin
  main/             the game's C++ (das modules it adds)
  gameBase/         settings, scenes, entity templates
  scripts/          das scripts: dng_empty/dng_empty.das loads everything else
  shaders/          shader setup; source/ holds the game's hooks into the renderer
  tools/            what daEditor runs of the game
  tests/            cpp, das, ecs and scenario tests
```

Files starting with `_` (`prog/_engine.jam`, `prog/_libs*`, `_engine.cmd`, ...) are written by `python project.py
setup` from `engine.blk` and the lib lists; every build runs it, they are not committed.

## The engine

`python project.py relink <engine dir>` points `engine.blk` at another checkout (`--absolute` stores an absolute path;
across drives it always is). jam output goes to the engine's `_output`, shader intermediates to this project's `_output`.

## Libraries

Add or remove engine libs in `prog/danetgamelibs.txt` (and `prog/gamelibs.txt`), then build: setup regenerates the jam,
vromfs, template, das and shader lists for them. Libs with an `_init.das` are loaded by `load_libs()` in
`scripts/dng_empty/dng_empty.das`; some need their entity templates created by a scene (see the lib's `templates/`).

## Tests

```bash
python project.py test                       # build and run every test target
python project.py test --layer ecs,das       # some layers
python project.py test -k dng_empty.ecs -v   # one target, verbose
```

| Dir | Layer | What |
|---|---|---|
| `prog/tests/cpp` | cpp | Catch2 tests of C++ code and data files |
| `prog/tests/das` | das | dastest tests of pure das logic, no game needed |
| `prog/tests/ecs` | ecs | `[ecs_test]` functions in the dedicated server: entities, systems, frames |
| `prog/tests/scenarios` | scenario | `[ecs_test]` functions in the client: input, rendering, screenshots |

Reports (HTML, JUnit, JSON) go to `<engine>/_output/test_results/<run>/`. See `<engine>/_docs/source/testing`.

## Assets

`develop/assets` holds the game's source assets; `python project.py build assets` (or `develop/dabuild`) exports them
into packs in `game/content/dng_empty/res`, which the game loads (settings.blk `addons{}`). `.folder.blk` there holds
the export rules. `develop/assets/base` has placeholders for the textures the renderer looks up by name (stars, moon,
strata clouds, the paint palette): replace them with real art under the same names.

## Tools

`develop/daEditor` opens the editor on this project; levels go to `develop/levels`. `develop/daViewer` browses the
assets in `develop/assets`, `develop/dabuild` exports them into the game (also `python project.py build assets`).
The editor renders levels with the game's renderer: run `python project.py build shaders vromfs tools` after changing
shaders, scripts or game data so its snapshot (`tools/snapshot`) is current.
