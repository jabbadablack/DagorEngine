# @GAME_NAME@ — single-player starter

Open `CMakeLists.txt` in Rider 2026.1+ or CLion, then build `@GAME_NAME@` and run
`@GAME_NAME@_run`. On Windows, you can also open `@GAME_NAME@.sln` in Visual Studio.
The engine is referenced in place; game code, settings and outputs stay here.

Edit `prog/main.cpp` for game update/rendering and `game/settings.blk` for runtime
settings. Both game and editor modes show a small wireframe scene. F2 switches
the scene inspector; F10 switches free camera. Fly with WASD, E/C and the mouse,
with Shift for speed. In the editor hold RMB over the viewport to fly. The
inspector selects/adds/deletes objects and edits names, positions and sizes.
Save/Load writes `game/scenes/starter_scene.blk`. Close the window or press Escape
to exit. Outputs go to `game/<platform>-<architecture>`.

Editor and free camera are included in the normal dbg/dev executable. No
separate targets or rebuilds are needed: press F2/F10 during play. Optional
`-editor` / `-freecam` arguments select an initial mode. Release omits these
development tools. The ImGui inspector
uses the engine's testGI shader bundle under `samples/testGI/game/compiledShaders`;
install or build those shaders with engine setup. `editorShaderPrefix` in settings
can override it. The free camera uses the same Dagor flight integrator as testGI.

The Jamfile selects DX11 on Windows, Vulkan on Linux and Metal on macOS.
Use the matching engine devtools setup on each host. Native Linux/macOS builds
must be verified on those hosts. The generated absolute engine reference can be
changed in `CMakeLists.txt`, `prog/jamfile` and `prog/@GAME_NAME@.vcxproj` if the
engine checkout is moved.
