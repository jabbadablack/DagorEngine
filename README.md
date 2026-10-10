## How to Build: Environment
Requirements for building and using the Dagor Engine toolkit: Windows 10 (x64), 16 GB of RAM, 200 GB of HDD/SSD space.

* Install Git: https://git-scm.com/download/win
* Install Python 3.8 or newer
* If you plan to use the FMOD sound library, also install FMOD Studio SDK 2.02.15

Create a project folder at the root of any drive (the folder name should not contain spaces or non-Latin characters).
```
md X:\develop && cd X:\develop
```

Clone the Dagor Engine source code:
```
git clone https://github.com/Prose-Studio/DagorEngine.git
cd DagorEngine
```

Everything else is done with `dng.py` in the DagorEngine root (`python dng.py <command> -h` lists the options of a command):
```
python dng.py devtools X:\develop\devtools          the build toolkit (once, then restart the console)
python dng.py build                                 the engine tools, dargbox and the project template
python dng.py new --name MyGame --dest ..\MyGame    a game project of your own
python dng.py test                                  the engine tests
```

## How to Build: Build Toolkit

Run `dng.py devtools`. It downloads, installs and configures the build toolkit. Give it the path of the build toolkit folder; it creates the folder if it doesn't exist, and skips what is already set up when run again.

```
python dng.py devtools X:\develop\devtools
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

## How to Build: Build from Source Code

Build from the DagorEngine root:
```
python dng.py build
```

This builds the engine toolkit (`cdk`), the `dargbox` UI tool and the `dngEmpty` project template from the source code. This process may take a considerable amount of time.
After the tools are built, each project's resources are built with daBuild and the other tools.
The data the tools load at runtime and that is not built (the editors' `commonData`, dargbox's fonts and UI, ...) is part of the repository, in `prog/tools/toolsData`, and the build copies it into `tools/`: nothing has to be downloaded.

Then create a game project with `python dng.py new`, see [Creating a Project](_docs/source/getting-started/new_project.md).

Projects: `cdk`, `dargbox`, `dngEmpty`, `physTest`, `skiesSample`, `testGI`, `outerSpace`, `dngSceneViewer`, or `samples` for all of the samples.
`-c` limits the components to build, `code`, `shaders`, `assets`, `vromfs`, `gui`, `tools` (default: everything each project builds), and `--arch` sets the target architecture, e.g. `x86_64`, `arm64`, `x86` (default: depends on the host OS and the jamfile).
Example: `python dng.py build dngSceneViewer -c code -c shaders` builds only code and shaders for the **daNetGame-based Scene Viewer** project.

You can also run a project's own build script, `prog/build.py` in its directory, with the same components and `arch:<arch>`, e.g. `python outerSpace/prog/build.py code arch:x86_64`, or the direct build commands:
* **To build code**, navigate to the `X:\develop\DagorEngine\samples\skiesSample\prog` folder and run the `jam` command (it builds `jamfile` script found in that folder).<br>After building the executable file will be placed in the `skiesSample\game` folder.<br>
* **To build shaders**, navigate to the `X:\develop\DagorEngine\samples\skiesSample\prog\shaders` folder and run any of `compile_shaders_*` scripts.<br>After building the shader-dump file will be placed in the `skiesSample\game\compiledShaders` folder.<br>
* **To build resources**, navigate to the `X:\develop\DagorEngine\samples\skiesSample\develop` folder and run the `dabuild.cmd` script.<br>After building the game resources will be placed in the `skiesSample\game\res` folder.<br>

## Samples (optional)

The assets of the samples are not in the repository. They are Gaijin's downloads under Gaijin's non-commercial content license (see `outerSpace/LICENSE.txt`); unpack the ones you want into the DagorEngine root with an archiver that reads .7z files, e.g. [7-Zip](https://www.7-zip.org/):
* [samples-base.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.09.20/samples-base.7z) - the assets of skiesSample, testGI and physTest
* [outerSpace-devsrc.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.09.20/outerSpace-devsrc.7z) - the assets of the Outer Space sample game
* [dngSceneViewer.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.09.20/dngSceneViewer.7z) - the east_district scene for dngSceneViewer (windows-x86_64 executables included)

`python dng.py build` skips the samples; name them to build them, `python dng.py build --list` shows whose content is unpacked:
```
python dng.py build samples
python dng.py build outerSpace dngSceneViewer
```

The directory structure of a sample:
```
X:\develop\DagorEngine\samples\skiesSample\game
                              \skiesSample\develop
                              \skiesSample\prog
```

* prog - game source code
* develop - initial assets
* game - directory where assets are placed after building and game executable files are located

### Basic dagor samples

* Offline scene viewer : **East District**<br>
  [Code](https://github.com/Prose-Studio/DagorEngine/tree/main/samples/dngSceneViewer/prog) and built scene data [east_district-dagor-prebuilt.tar.gz](https://dagorenginedata.cdn.gaijin.net/rel-0ebc89d5d795f3f96324843abf72c5ca7b8555cf/east_district-dagor-prebuilt.tar.gz) to be unpacked to DagorEngine root<br>
  **east_district-dagor-prebuilt.tar.gz** also contains prebuilt viewer app (for windows, macOS and linux) to run sample at once<br>
  [Demos of a new Gaijin’s game showcase Dagor Engine power](https://gaijinent.com/news/demos-of-a-new-gaijins-game-showcase-dagor-engine-power)<br>
  [East District review on YouTube](https://youtu.be/miABl6aekBA)
* Multiplayer sample: **Outer Space**<br>
  [Code](https://github.com/Prose-Studio/DagorEngine/tree/main/outerSpace/prog) and source (develop) files [outerSpace-devsrc.7z](https://dagorenginedata.cdn.gaijin.net/head-2026.09.20/outerSpace-devsrc.7z) to be unpacked to DagorEngine root<br>
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
