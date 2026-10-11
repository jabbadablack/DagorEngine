# CMake port: decisions taken from the jam inventory

`inventory.py` (jam dry runs of every root in `roots.txt` and of the unit tests) shows what the jam roots of one
CMake tree build differently. These are the decisions for each finding. They apply when the area is ported (the phase
is in brackets). Kept until jam is deleted; the lasting rules move to `_docs/source/build-system/`.

## The trees and their global settings

jam settings that are global per root become per-tree options set by presets:

| Tree (`DAGOR_VARIANT`) | jam output dir of its roots | CMake tree settings |
|---|---|---|
| `tests` | mostly `vc17 ~s4 ~ex`; daFrameGraph and metronome tests `clang ~m ~s4 ~ex ~c` | clang-cl by default, MSVC through `windows-msvc-tests`. The D3D-multi tests (`~m`) and the checked containers (`~c`) are set per test [1] |
| `cdk` | `clang ~s2 ~fp ~ex` (static kernel) | `DAGOR_SSE=2` and `DAGOR_FP_MODEL=precise` on Windows, SSE4 elsewhere (`prog/tools/tools_setup.jam`) [2] |
| `editor` | `clang ~krnlimp ~s2 ~fp ~ex`, `~m` for the GUI tools | dynamic kernel plus the cdk settings. **daBuild and its exporter DLLs, and ddsxCvt2, link daKernel**, so they are in this tree, not in cdk; the host-tools sub-build builds both trees [2] |
| `dargbox` | `clang ~m ~s2 ~fp ~ex` | the cdk settings plus the D3D driver list [4] |
| `maxplug` | (Max SDK missing locally, not inventoried) | `/MD`, exceptions, RTTI [4] |

- **Tools jam always builds in `rel`** (binBlk, ddsx2dds, ddsxCvt and the pc/ios/and ddsxConv plugins: `-sConfig=rel` in
  their jamfiles). In CMake they build in the tree's configuration, keeping jam's file names (`NO_CONFIG_POSTFIX`).
  Dev is optimized too, so the only difference is that their asserts stay on in Dev [2].
- **dolphin and whale** (the parser generators of the shader compilers) are built `rel` with exceptions, SEH and RTTI.
  These become per-target `EXCEPTIONS SEH` and `RTTI ON`; they keep the tree's SSE level (jam's SSE4 there only came
  from the defaults) [2].
- **Linux tools and samples** add `-march=haswell` in jam (`samples_setup.jam`, `MArch`). It becomes `DAGOR_MARCH`
  (default `haswell` for linux-x86_64 games and samples, `-default-` for e2k, Astra and ROSA) [3].

## Libraries built under more than one name in one tree

| Library dir | jam variants | CMake |
|---|---|---|
| `engine/memory`, `3rdPartyLibs/memAllocators/dlmalloc` | `~RTL`, `~dlmalloc`, `~mimalloc`, `-nd`, `-d1`, `-d` | selector libraries, one per allocator backend and debug level: a program links the one it uses [1] |
| `engine/shaders` | `shaders-cs`, `shaders-2`, `shaders-2-cs`, `-stboth` | the shader-vars backends (stub, mock) and the camera stub become selector libraries; `CppStcode` is a tree option [2] |
| `3rdPartyLibs/eastl` | `eastl`, `eastl_local` | two targets in one directory (`3rdPartyLibs.eastl`, `3rdPartyLibs.eastl.local`) [1] |
| `engine/perfMon` | `perfMon`, `perfMon~noGPU` | selector library `engine.perfMon.noGPU` [1] |
| `gameLibs/render/daFrameGraph` | `daFrameGraph`, `~ut` | the unit-test flavor as its own target [1] |
| `engine/lib3d`, `commonFx/commonFxGame`, `engine/imgui`, `3rdPartyLibs/imgui`, `tools/libTools/propPanel`, `engine/drv/vr_device`, `engine/lowLatency`, `engine/profilerTracker`, `daEditorX/services/dynRenderSrv` | `~t`, `~gz`, `~ete`, `-stub`, `-comp`/`-nocomp`, `~vr` | one target per flavor in the library's directory, linked by the programs that used it [2, 4] |
| `engine/math`, `engine/anim`, `engine/animChar`, `engine/phys/fastPhys` | `~pm1-1000` (`DagorMath_MEASURE_PERF`) | measure-perf flavors; ported only if a program still uses them [4] |
| `engine/drv/drv3d_pc_multi`, `drv3d_commonCode` | four driver lists (`~stub~DX11`, `~DX11~DX12`, ...), `~nDX12`, `~nSpirV` | `DAGOR_D3D_DRIVERS` for the tree; the editor programs share one list [4] |
| `gameLibs/vehiclePhys` | `-BULLET~bt3`, `-JOLT` | one target per physics engine (`PhysName`), linked by the program that used it [4] |

The `~zng` (zlib-ng), `-1.4.5` (zstd) and `-3.x` (OpenSSL) suffixes are not variants: jam allowed other versions, and
CMake builds only these.

jam's `if $(X) in a b` is true when `X` is unset, so a few conditions did the opposite of what they read like. The
CMake build keeps what jam built: `CppStcode` defaults to `both` (the shader stcode compiled in and validated), and
quirrelHost's `ENABLE_RE_USE=0` applies only under the sanitizers other than ASan. The tests tree on every platform
uses the multi-driver interface, which jam's test driver lists (stub with DX12 or Vulkan) gave it on Windows and Linux.

The tool trees (Phase 2):
- The cdk tree has the static-kernel tools; the editor tree (DAGOR_KERNEL_LINKAGE dynamic) has daKernel, daBuild with
  its plugins and ddsxCvt2. `cmake --install <tree> --component cdk` puts them into tools/dagor_cdk/<platform>-<arch>
  as jam did; `--component cdk-data` adds prog/tools/toolsData and the GUI shader dumps (dagor_add_shaders).
- Generated sources go into the build dir, not next to their inputs: the dolphin/whale parsers of the shader
  compilers, the ISPC headers, stringified files. A build step removes stale copies jam left in the source tree.
- Trees that run CDK tools without building them (projects, cross builds) get them through dagor_host_tool():
  DAGOR_HOST_TOOLS_DIR, or a locked on-demand build of the engine's host cdk tree (prog/cmake/DagorHostTools.cmake).
- Programs choose what jam set with globals for a whole build through link choices: DAGOR_MEASURE_PERF (anim, animChar,
  fastPhys, math), DAGOR_LINUX_GUI (also bindQuirrelEx); flavors where only one program uses another build
  (mimalloc:nodebug and engine/memory:mimalloc.off for the shader compilers, the emb builds for gameLibs/assets_import).
- A target's own options come after the tree's and its warning set's, as jam ordered them (CMake would put the options
  of linked interface libraries last).
- MSVC links without identical-code folding (/OPT:NOICF): daFrameGraph compares the addresses of functions with the
  same code, which link.exe would fold; lld-link folds only what clang marks safe (/OPT:SAFEICF).
- Checked against jam's tools: the GUI shader dumps (DX11, DX12, SPIR-V) are byte-identical; daBuild's output for
  outerSpace is identical except riDesc.bin, which jam's own daBuild writes differently on every run.

The game trees (Phase 3):
- A project's top-level CMakeLists.txt reads the engine root from engine.blk (DAGOR_ENGINE_ROOT overrides it), includes
  the engine's DagorBootstrap.cmake and adds its prog/. The project's presets are self-contained (<platform>-client,
  <platform>-dedicated): they set cache variables only, so they never name the engine's path.
- As with jam, the executables go to <project>/game/<platform>-<arch> and the built content into <project>/game; only
  intermediates are in build/<preset>.
- daNetGame's switches (setup.jam's Have*, BVH, the D3D drivers, exceptions off, -march=haswell on Linux x86_64,
  TIME_PROFILER_ENABLED=0 on the Linux servers) are tree settings (DagorOptions.cmake, DagorGame.cmake). Those jam
  turned off in Rel only (the editor, webui, ImGui, the console) are generator expressions: daNetGame and the libraries
  build the parts of some configurations only, and the entity systems and pulls of those parts follow.
- dagor_add_dng_game() generates what game.jam wrote (gameproj::, the auth keys, the pull of every module); the libs of
  danetgamelibs.txt / gamelibs.txt add themselves to the game through their _lib.cmake (jam's _lib.jam), and to the
  AOT compiler through their _aot.cmake. Game modules (build_module.jam) are dagor_add_dng_module().
- daFrameGraph's daScript and daECS integration (jam's DAFG_ENABLE_* globals) is the default target's in game trees
  (DAGOR_DAFG_FEATURES); BVH's feature switches are DAGOR_BVH_STUBS.
- daScript AOT: a sub-build of the project's own tree with DAGOR_DAS_AOT_COMPILER makes <game>-aot (Dev, under a lock,
  in build/_host/aot-<host>), as jam's AotJamfile sub-build did; the game tree compiles the DAS_AOT scripts with it in
  batches of 10 and names each target's pull (DAS_AOT_PULL).
- daNetGame uses its precompiled header in every configuration (jam: Dev and Dbg); the Ninja generator cannot have a
  precompiled header in some configurations only.
- On Windows, CMake 4.2's SHORT intermediate dirs keep the objects of a project tree's engine dirs under MAX_PATH.
- Checked: the Windows dedicated server of dng-empty registers the same component types, components and entity systems
  as jam's (its startup log is identical but for dates), and the 78 entity systems' generated code it compiles is
  byte-identical to the committed .gen.es.cpp files. A jam build from a project rewrites those committed files with
  absolute paths; the CMake build never writes into the source tree.
