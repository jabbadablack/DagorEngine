# Creating a Project

`new_project.py` in the engine root creates a game project from a template in `templates/`. The project can live
anywhere: its `engine.blk` names the engine checkout it is built with, and the build, the game and the tools find the
engine through it.

```bash
python new_project.py --name MyGame --dest ../MyGame
cd ../MyGame
python project.py build
game/client.cmd
```

## Options

| Option | Meaning |
|---|---|
| `--name` | PascalCase name (`MyGame`): macOS bundle and Windows manifest names |
| `--codename` | lowercase name of the executables, the main vromfs and script dirs (default from `--name`: `my_game`) |
| `--title` | human readable name: window title, executable info (default from `--name`: `My Game`) |
| `--company` | reverse domain name for the bundle id `<company>.<name>` (default `com.example`) |
| `--dest` | the project dir: new or empty, ASCII without spaces (default `../<name>` next to the engine) |
| `--template` | template id (`--list` shows them; default `dng-empty`) |
| `--absolute-engine-path` | `engine.blk` stores an absolute path (by default relative, absolute only across drives) |
| `--no-git` | no `git init` in the new project |
| `--dry-run` | print the files it would create |

The engine's tools have to be built (`python dng.py build cdk` in the engine) before the project builds its
shaders, vromfs and assets.

## The dng-empty template

An empty daNetGame game: a client and a dedicated server, an empty default world (sky and lighting, no level data)
with a camera, one sample entity system, the scripts of the tools (daEditor, daViewer, dabuild, daImpostor) and a test
target of every [test layer](../testing/overview.md). Its `README.md` describes the layout.

The template is under the engine's license, like `prog/`. It takes nothing from the content of the sample games
(`outerSpace`, the downloadable sample assets), which is licensed differently: the textures the renderer needs by name
(stars, moon, strata clouds, a paint palette) are generated placeholders in `develop/assets/base` to be replaced, and
water, glass scratches, fluid wind and UI fonts are off until a game brings their assets (see `gameparams.blk` and
`settings.blk` in the template).

`templates/dng-empty` is itself a buildable project inside the engine (`engine.blk` points at `../..`): CI builds and
tests it, and changes to it are made and checked there before they reach new projects. The names in it
(`dng_empty`, `DngEmpty`, `Dng Empty`, `com.dagor.DngEmpty`) are the tokens `template.blk` lists; the generator
replaces them in file names and text files, and refuses to finish if one is left.

## Linking a project to an engine

```text
engineRoot:t="../DagorEngine"   // engine.blk: relative to the project, or absolute
```

`python project.py relink <engine dir>` rewrites it and regenerates the files that depend on it:

| Generated file | For |
|---|---|
| `prog/_engine.jam` | jam: `EngineRoot`, `ProjectProgLocation` (the jam `Location` of the project's `prog`) and `Root` |
| `_engine.cmd`, `_engine.sh` | the develop scripts: `DAGOR_ENGINE_ROOT` and `DAGOR_CDK_DIR` |
| `prog/_libs*` | the libs of `prog/danetgamelibs.txt` and `prog/gamelibs.txt`: jam, AOT jam, vromfs, templates, das init, shaders |

`python project.py setup` writes them; `project.py build` runs it first, so they are never stale. They are not
committed. Inside the engine, data files name engine paths through the `%engine` named mount, which the engine resolves
from `engine.blk` too (from the first `engine.blk` or engine checkout above the current dir, unless the
`DAGOR_ENGINE_ROOT` environment variable names one): settings `mountPoints`, shader and vromfs configs and
`application.blk` use `%engine/prog/...` and work wherever the project is.

A project on another drive than the engine stores an absolute engine path and gets an absolute jam `Location`
(see `LocationDir` in `prog/_jBuild/jCommonRules.jam`).
