## How to Build: Environment

For Rider, CLion and portable CMake workspaces, open
[`prog/_jBuild/CMakeLists.txt`](prog/_jBuild/CMakeLists.txt) and see
[IDE workspaces and single-player/multiplayer templates](_docs/ide_workspaces.md).

For Visual Studio 2022/2026 and the Visual Dagor extension, see
[Visual Studio setup, builds and IntelliSense](_docs/visual_studio.md).

Requirements for building and using the Dagor Engine toolkit: Windows 10 (x64), 16 GB of RAM, 200 GB of HDD/SSD space.

* Install Git: https://git-scm.com/download/win
* Install 7-Zip: https://www.7-zip.org/
* Install Python 3
* If you plan to use the FMOD sound library, also install FMOD Studio SDK 2.02.15

Create a project folder at the root of any drive (the folder name should not contain spaces or non-Latin characters).
```
md X:\develop && cd X:\develop
```

Clone the Dagor Engine source code and samples:
```
git clone https://github.com/GaijinEntertainment/DagorEngine.git
cd DagorEngine
```

Run `dng.py bootstrap --install-devtools --skip-build`. This script will download, install, and configure the build toolkit. You should provide the path to the build toolkit folder as an argument, and the script will create this folder if it doesn't exist.

```
python3 dng.py bootstrap --install-devtools --skip-build --devtools X:\develop\devtools
```

If the script is not run as an administrator, installers of certain programs may request permission for installation, which you should grant. If you plan to use plugins for 3ds Max, press 'Y' when the script asks if you want to install the 3ds Max SDK. The script will also ask to add the path X:\develop\devtools to the PATH environment variable and set the GDEVTOOL variable to point to this folder.

After the script completes its work, the X:\develop\devtools folder will be configured with the following SDKs and tools:

* aftermath-2025.5.0.25317 - NVIDIA Nsight Aftermath
* Agility.SDK.1.619.3 - DirectX 12 Agility SDK
* AGS.SDK.6.3.0 - AMD GPU Services
* astcenc-4.6.1 - Adaptive Scalable Texture Compression (ASTC) Encoder
* DXC-1.8.2505.1 - DirectX Compiler
* FidelityFX_SC - a library for image quality enhancement
* fmod-studio-2.xx.xx [optional] - FMOD sound library
* ispc-v1.23.0-windows - Implicit SPMD Program Compiler
* LLVM-21.1.8 - C/C++ compiler and libraries (Clang)
* max2026.sdk - 3ds Max 2026 SDK
* nasm - netwide assembler ver 2.x
* openxr-1.1.54 - library for AR/VR
* streamline-2.14.1 - NVIDIA SDK for DLSS, DLAA, Reflex, etc.
* vc2019_16.11.34 - C/C++ compiler and libraries (MSVC)
* vc2022_17.14.4 - C/C++ compiler and libraries (MSVC)
* win.sdk.100 - Windows 10 SDK
* win.sdk.81 - Windows 8.1 SDK
* ducible.exe - a tool to make builds of Portable Executables (PEs) and PDBs reproducible
* pdbdump.exe - a tool for dumping the content of PDB files
* jam.exe - a small build tool (used in DagorEngine instead of Make and similar tools)

Restart the command line console to make the new environment variables available.

## How to Build: Prebuilt Binaries

You will need to download and extract additional binary files (as of 2026/08/16) from the CDN into the X:\develop\DagorEngine folder:
* [tools-base.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/tools-base.7z) - contains initial data for tools
* [samples-base.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/samples-base.7z) - contains initial assets that will be compiled into binary files that will be loaded by the game (samples)
* [outerSpace-devsrc.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/outerSpace-devsrc.7z) - contains initial assets for OuterSpace sample project
* [dngSceneViewer.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/dngSceneViewer.7z) - contains binary data for east_district sample with dngSceneViewer (windows-x86_64 executables also included)

More downloads in the repository [https://github.com/GaijinEntertainment/DagorEngine/releases](https://github.com/GaijinEntertainment/DagorEngine/releases) with prebuilt binaries (may be a bit outdate):

* [tools-prebuilt-windows-x86_64.7z](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/tools-prebuilt-windows-x86_64.7z),
  [tools-prebuilt-windows-arm64.7z](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/tools-prebuilt-windows-arm64.7z),
  [tools-prebuilt-linux-x86_64.tar.gz](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/tools-prebuilt-linux-x86_64.tar.gz),
  [tools-prebuilt-macOS.tar.gz](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/tools-prebuilt-macOS.tar.gz) - contains the prebuilt engine toolkit

The directory structure should look like this:
```
X:\develop\DagorEngine\tools\...

X:\develop\DagorEngine\samples\skiesSample\game
                              \skiesSample\develop
                              \skiesSample\prog

X:\develop\DagorEngine\samples\testGI\game
                              \testGI\develop
                              \testGI\prog
```

* prog - game source code
* develop - initial assets
* game - directory where assets are placed after building and game executable files are located

## How to Build: Build from Source Code

Install Python 3.10+, CMake 3.24+ and Ninja, with CMake and Ninja on `PATH`.
Bootstrap installs mandatory tool data if missing. To install it manually, unpack
[tools-base.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/tools-base.7z) to the DagorEngine root.

If you are going to run samples unpack [samples-base.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/samples-base.7z) to DagorEngine root (if you plan to only build EXE and shaders these binary data are not mandatory).

To build and run OuterSpace sample project unpack also [outerSpace-devsrc.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/outerSpace-devsrc.7z) to DagorEngine root.

Use the single root entry point for engine and game development:

```sh
python dng.py bootstrap                         # CMake configure + engine tools + default project
python dng.py bootstrap --skip-build            # Configure using an existing toolchain
python dng.py build --project testGI
python dng.py new --name MyGame --template singleplayer --directory ../MyGame
cd ../MyGame
python prog/build.py                            # This game
python prog/build.py --no-build --run
python prog/build.py --level-editor
python prog/build.py --asset-viewer
```

CMake entry files remain under `prog/_jBuild`. Jam is the native build backend;
`dng.py` uses CMake to configure and build its targets. The old platform installer
and sample build recipes are internal modules under `prog/_jBuild/bootstrap`,
not additional root commands. See [_docs/ide_workspaces.md](_docs/ide_workspaces.md).

New templates are independent of sample projects and assets. They provide
original graybox meshes, daScript gameplay, and Quirrel/daRg embedded editor UI.
Editable sources stay in `prog`/`develop`; build outputs stay in `game`.

### Basic dagor samples

* Offline scene viewer : **East District**<br>
  [Code](https://github.com/GaijinEntertainment/DagorEngine/tree/main/samples/dngSceneViewer/prog) and built scene data [east_district-dagor-prebuilt.tar.gz](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/east_district-dagor-prebuilt.tar.gz) to be unpacked to DagorEngine root<br>
  **east_district-dagor-prebuilt.tar.gz** also contains prebuilt viewer app (for windows, macOS and linux) to run sample at once<br>
  [Demos of a new Gaijin’s game showcase Dagor Engine power](https://gaijinent.com/news/demos-of-a-new-gaijins-game-showcase-dagor-engine-power)<br>
  [East District review on YouTube](https://youtu.be/miABl6aekBA)
* Multiplayer sample: **Outer Space**<br>
  [Code](https://github.com/GaijinEntertainment/DagorEngine/tree/main/outerSpace/prog) and source (develop) files [outerSpace-devsrc.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/outerSpace-devsrc.7z) to be unpacked to DagorEngine root<br>
  Prebuilt game (executables, shaders, vromfs, gameres) is available as [outerSpace-prebuilt-fullsrc.tar.gz](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/outerSpace-prebuilt-fullsrc.tar.gz)

### Documentation
  Automatically generated [Dagor Documentation](https://gaijinentertainment.github.io/DagorEngine/) contains general architecture description, API reference, tutorials and manuals.<br>
  It is not complete yet and will be extended.

## Open-source roadmap

We are going to open-source more parts of our Engine and tools.
These are general and broad plans for next year, can be changed.

### Documentation

* how to work with dagor assets
* daNetGame framework
