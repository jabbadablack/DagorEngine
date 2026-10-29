# @GAME_NAME@ — multiplayer starter

Open `CMakeLists.txt` in Rider 2026.1+ or CLion, or `@GAME_NAME@.sln` in Visual
Studio on Windows. Build the `@GAME_NAME@` target. Run one instance with no
arguments to host on UDP port 27015, then another with `-connect:127.0.0.1` to
connect locally. Use `-connect:<host>` for another machine and `-port:<number>`
to select another port on both instances.

The window starts blue and turns green after a versioned ENet handshake.
The host accepts up to 16 peers. Network events are processed without blocking
the game loop. Logs record host/client handshake completion and disconnects.
F2 switches the scene inspector; F10 switches free camera. Fly with WASD, E/C,
mouse and Shift, or hold RMB over the editor viewport. Select/add/delete objects
and edit transforms in the inspector; Save/Load persists
`game/scenes/starter_scene.blk`. Close the window or press Escape to exit.

Both templates share this editor and the engine flight-camera integrator. Use
the `@GAME_NAME@_editor` / `@GAME_NAME@_freecam` CMake targets or `-editor` /
`-freecam` arguments. Visual Studio starts in editor mode. The inspector uses
the engine's testGI shader bundle; install/build the sample shaders with engine
setup, or override `editorShaderPrefix` in settings. Scene editing is local;
extend the template networking protocol to replicate your game's scene changes.

This is a networking foundation: add your game state, authoritative simulation,
input messages and replication in `prog/multiplayer.cpp` and `prog/main.cpp`.
It does not include a finished game or account/session services. Runtime settings
live in `game/settings.blk`; outputs go to `game/<platform>-<architecture>`.

The template selects DX11 on Windows, Vulkan on Linux and Metal on macOS and
references the engine in place. Install matching engine devtools on each host.
Native Linux/macOS builds must be verified on those hosts.
