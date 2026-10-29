# daScript-first gameplay

Write gameplay as ECS systems under `prog/scripts/game/es`; the entry loader is
`prog/scripts/game/main.das`. Entity archetypes and replicated components belong
in `prog/gameBase/gamedata/templates`, and runtime scenes in `gamedata/scenes`.
The native host is the engine's daNetGame application, so there is no generated
C++ game loop to edit for ordinary gameplay.

Quirrel/daRg handles UI and the embedded entity editor. `prog/scripts/ui/main.nut`
loads the shared engine daEditor UI and maps F2/F10 to the native editor/camera
commands. Editor tools are available in ordinary debug/dev builds. The daScript
project resolver imports engine modules through named mount points defined in
settings; sources never live in `game`. Development config enables source mounts
so the engine's script reload facilities can be used without rebuilding native
code. Release uses packaged VROMFS and omits the embedded development editor.

All starter meshes are generated original graybox geometry. No sample assets,
levels, scripts or shader bundles are copied. The only bundled font is JetBrains
Mono, together with its OFL notice. Shader compilation imports engine-owned code.
