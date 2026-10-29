# Engine and game workspaces

`dng.py` is the root command for bootstrap, CMake builds, content and project creation.
CMakeLists.txt, CMakePresets.json and cmake/ remain in `prog/_jBuild`.

```sh
python dng.py bootstrap --install-devtools --devtools ../devtools
python dng.py new --name MyGame --template singleplayer --directory ../MyGame
cd ../MyGame
python prog/build.py
python prog/build.py --no-build --run
```

Use `multiplayer` for local host/client launchers over daNetGame networking. Both
variants use the engine's daScript ECS runtime and Quirrel/daRg editor; no sample
project, asset pack or shader dump is copied or required. Engine shader source
is imported by the project's shader build descriptions. Cube, sphere and plane
DAG meshes are generated original geometry. JetBrains Mono and its OFL notice
are bundled for UI. Content builds generate shaders, assets, fonts and VROMFS.

Each game owns its solution, CMake presets and `prog/build.py`. Its launchers call
that local script; invoking the engine CLI is optional after creation.

Open a generated CMakeLists.txt in Rider/CLion, or its solution in Windows Visual
Studio. `dng.py configure` configures a Ninja workspace; `build` and `rebuild`
invoke CMake targets, which use Jam internally. `dagor_tools` builds required
native tools. `dng.py bootstrap --skip-build` configures an existing toolchain.
The optional devtools installer downloads/configures host dependencies.

Editor and free camera are part of the ordinary dbg/dev game executable. F2
invokes the engine entity editor; F10 invokes the engine flight camera. The editor
UI is the engine's shared Quirrel/daRg UI. `editor.cmd`/`.sh` launches it;
`level-editor`, `asset-viewer` and `ui-editor` open the native content tools.
The generated README and SCRIPTING.md describe editable source locations.

The machine-local registry under `_output/ide` tracks external projects without
creating a games directory in the engine. Existing directories are never
overwritten. `--directory` selects an external project for build/run/tool commands.
For engine work, `--project` selects a registered CMake target. Use `--dry-run` to
inspect CLI commands. Native Linux/macOS runtime validation requires those hosts.
