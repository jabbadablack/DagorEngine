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
