# Visual Studio and Visual Dagor

For Rider/CLion, native host builds and standalone single-player/multiplayer
templates, see [Portable IDE workspaces](ide_workspaces.md). The CMake entry point
is `prog/_jBuild/CMakeLists.txt`; the Visual Studio solution remains Windows-only.

Open `DagorEngine.sln` with Visual Studio 2022 or 2026, Desktop development with
C++, and the Visual Dagor extension installed. The integration currently targets
Windows x86_64 with `dbg`, `dev`, and `rel` configurations. It runs the existing
Jam build, using the compiler and SDK versions configured by the engine's
devtools rather than Visual Studio's C++ compiler selection.

## Initial setup and regeneration

From the engine root, run in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File prog\_jBuild\msbuild\setup.ps1
```

The default extension source directory is `..\DagorVisualStudioTools`. This
checkout needs the Visual Studio 18 build fixes. Pass `-ExtensionRoot <path>` if
it is elsewhere. Setup builds its MSBuild task project, copies the task and its
runtime dependencies to `prog\_jBuild\msbuild\bin`, generates solution/filter
files, and asks Jam for compiler settings in all configured executable/configuration
combinations. It does not compile the engine or rebuild the VSIX.

`GDEVTOOL` selects the devtools directory; the fallback is `..\devtools`. The
integration prefers its bundled Python and Jam. `prog\platform.jam` remains the
authority for the engine's compiler/SDK setup.

Run setup again after changing Jam settings or adding/removing source files.
For just source lists and folder filters, run:

```powershell
& ..\devtools\python3\python.exe prog\_jBuild\msbuild\generate_projects.py
```

Generated file lists, IntelliSense props and compilation databases live in
`_output\visualstudio`; task binaries and `.vcxproj.filters` files are also
ignored by Git. The explicit file lists let Visual Studio display source files
without unsupported wildcard project items. Keep the tracked `CppSource` and
`CppHeader` patterns when extending a project; regenerate their explicit lists.

## Build, debug and browse

1. Open `DagorEngine.sln` and choose `dev | x64` for the normal development build.
2. Set an executable project as the startup project, such as `testGI` or
   `outer_space`. `Dagor Engine` is the shared source browser, not an executable.
3. Build the selected project, then use F5 with the configured local debugger.
   Each project's executable path and working directory follow its current
   Jamfile. Runtime assets still come from the normal engine setup.

The solution includes testGI, skiesSample, dng_scene_viewer, outer_space,
ShaderCompiler2 (DX12), AssetViewer, daEditorX, dag2blk and dargbox, plus the shared engine
source project. Build Solution selects testGI by default. Build other projects
explicitly or enable them in Configuration Manager.

Visual Dagor recognizes `DagorProject` and `DagorSharedProject` capabilities and
the `SharedProject` property rule. It propagates startup-project definitions and
Jam arguments to the shared engine project. Generated include settings match
those arguments, including distinct tool Jamfiles sharing `prog\tools` as their
working directory. The main project IntelliSense context comes from an actual
translation unit in that project's Jam compilation database; individual
translation units can have additional flags.

Compile Selected Files (Ctrl+F7) uses Jam's exact command for the selected source,
including files selected in the shared project. Build normally first if the
source requires generated headers or a PCH. Sources outside the startup
project's build graph report an explicit error. The full database is available
at `_output\visualstudio\<project>\<configuration>\compile_commands.json`.

Build invokes Jam normally, Rebuild adds `-a`, and Clean invokes Jam's `clean`
target. For a command-only build validation, pass `/p:DagorJamOptions=-n`.

## Command line validation

Use full-framework MSBuild from Visual Studio, not `dotnet build`:

```powershell
$msbuild = 'C:\Program Files\Microsoft Visual Studio\18\Community\MSBuild\Current\Bin\MSBuild.exe'
& $msbuild DagorEngine.sln /p:Configuration=dev /p:Platform=x64 /nr:false
& $msbuild prog\tools\converters\dag2blk\dag2blk.vcxproj /p:Configuration=dev /p:Platform=x64 /nr:false
& ..\devtools\python3\python.exe prog\_jBuild\msbuild\validate.py --msbuild $msbuild
```

`validate.py` checks literal source lists, capabilities, all project/configuration
evaluations, absolute debugger paths, generated compilation databases and
startup-dependent shared include settings. Initial integration validation also
linked testGI and dag2blk and compiled a selected shared engine source through
VS18 MSBuild. The remaining executables' Jam graphs and compiler settings were
validated without full rebuilds.

The dag2blk project explicitly selects Clang, matching the other modern tool
projects and avoiding a PDB manager mismatch encountered with the local MSVC
devtools installation. Its output remains `tools\converters\dag2blk`, as specified
by its Jamfile. Console, Linux and mobile platform configurations are not exposed
by this Windows solution.
