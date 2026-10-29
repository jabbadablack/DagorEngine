# Portable IDE workspaces and project templates

The portable workspace lives at `prog/_jBuild/CMakeLists.txt`, with presets and
the CMake module beside it. Jam remains the build system; CMake supplies the IDE
project model and named build/rebuild/clean/run targets. No Visual Studio SDK,
MSBuild or VSIX is needed for this workspace.

Open that CMake file in Rider 2026.1+ (CMake support is Beta in 2026.1 and stable
in 2026.2), CLion, or another CMake IDE. Install Python 3.10+, CMake 3.24+, Ninja,
and the engine devtools for your host. Native Windows, Linux and macOS routes are
provided. Host compilers, SDKs and runtime assets still come from engine setup.

From the engine root:

```sh
cmake -S prog/_jBuild --preset dev -DDAGOR_ACTIVE_PROJECT=testGI
cmake --build _output/cmake/dev --target testGI
cmake --build _output/cmake/dev --target dargbox_run
```

Choose `DAGOR_ACTIVE_PROJECT` for the default build and code-analysis context.
`DAGOR_CONFIG` accepts dbg/dev/rel. `DAGOR_PLATFORM` defaults to the host's windows,
linux or macOS name, and `DAGOR_ARCH` defaults to the native architecture.
`DAGOR_JAM` can override Jam discovery; otherwise `GDEVTOOL` or `../devtools` is
used, followed by PATH. CMake's `Python3_EXECUTABLE` selects a particular Python.

Each executable has `<name>`, `<name>_rebuild`, `<name>_clean` and `<name>_run`
targets. The DX12-specific ShaderCompiler2 project is exposed only for Windows.
`dagor_index_only` is an excluded code-analysis target, not the engine build.
Build through the named Jam targets. CMake prints the active executable and
debugger working directory; use those in an IDE's custom native debug profile.

The build directory's `compile_commands.json` contains the real per-file Jam
compiler commands, including source/output arguments. It can also be opened in
CLion or consumed by clangd. The CMake code model uses the active project's main
translation-unit settings. Reconfigure after changing source lists or Jam
settings. The active Jamfile and engine platform configuration trigger automatic
reconfiguration when changed.

## Create a standalone game

Templates are under `templates/singleplayer` and `templates/multiplayer`.
Generated projects live at the location you choose, outside the engine source
tree by default. There is no engine `games` directory.

```sh
python prog/_jBuild/ide.py new --name MyGame --template singleplayer --directory ../MyGame
python prog/_jBuild/ide.py new --name NetworkGame --template multiplayer --directory ../NetworkGame
```

Both templates include CMake and Visual Studio entry points, a Jamfile, C++
startup/game-loop code, platform startup support and runtime settings. The
single-player template opens a small wireframe scene. Both templates have an
ImGui scene inspector (F2), Dagor free camera (F10), add/delete/transform controls,
and scene save/load. The inspector references the engine's testGI shader bundle;
install/build the sample shaders, or override `editorShaderPrefix` in settings.
The multiplayer template adds an ENet host/client
handshake through engine/daNet, bounded event processing and connection feedback.
Its window turns green only after the handshake succeeds. Run a host with no
arguments, then a client with `-connect:127.0.0.1`; `-port:27015` selects the port.
Game state replication and gameplay rules are left for your project.

Template projects also expose `<name>_editor` and `<name>_freecam` CMake targets.
Launch directly with `-editor` (or `-edit`) and `-freecam`. Visual Studio F5 starts
in editor mode. Controls follow the samples: WASD, E/C, mouse, Shift for speed;
hold RMB in the editor viewport to navigate. Inspector changes persist to
`game/scenes/starter_scene.blk`; they are local until your game adds replication.

Projects reference the engine checkout and write binaries under their own
`game/<platform>-<architecture>` directory. On Windows they must share a drive
with the engine because Jam uses relative source locations. Existing directories
and registered project names are never overwritten.

New projects are recorded in the machine-local
`_output/ide/project-registry.json`, so regeneration finds them without creating
project directories in the engine. An engine solution may reference them via
relative paths. On another machine, set `DAGOR_ENGINE_ROOT` in the environment or
as a CMake cache variable. Configuring the standalone CMake project registers it
with that engine and rebases its Jam paths automatically. Visual Studio users
must also update the engine import path in their vcxproj after moving checkouts.
Templates are tracked; machine-specific registrations are not.

In CMake IDEs, the `new_dagor_game` target uses `DAGOR_NEW_GAME_NAME`,
`DAGOR_NEW_GAME_TEMPLATE` and `DAGOR_NEW_GAME_DIRECTORY`. In Visual Studio, install
the updated personal-fork VSIX and choose **Tools > New Dagor Game...** to select
the same fields in a dialog. Visual Studio uses dev | x64; CMake supports native
host platforms independently.

## dargbox

The Visual Studio solution and portable workspace both include dargbox. Its
runtime working directory is `tools/dargbox`, not its architecture-specific
executable directory. Windows and Linux direct launches fall back to the parent
runtime directory when their current directory lacks settings. This fixes the
startup fatal caused by missing settings and shader paths when opening the
executable directly. Shader assets must still be present from engine setup.

## Validation scope

Windows validation built and ran both generated templates. The multiplayer test
started a local host and client and verified successful handshakes and zero exit
codes. CMake configured the relocated workspace and built dag2blk through Jam.
Editor runtime tests check mode switching, held-key repeat suppression, camera
movement and stopping, and scene persistence, in addition to rendering the UI.
dargbox was rebuilt and directly launched, loading its shaders, fonts and GUI
without the previous fatal. The extension VSIX builds successfully.

Unit tests validate template selection, path/name handling, platform/architecture
routing and standard compilation-database output. Linux/macOS build paths and
startup sources are provided, but native builds and rendering on those hosts
have not been run from this Windows machine.
