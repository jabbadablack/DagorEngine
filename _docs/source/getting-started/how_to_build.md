# How to Build

## How to Build: Environment

```{important}
Requirements for building and using the Dagor Engine toolkit:
- Windows 10 (x64)
- 16&nbsp;GB of RAM
- 200&nbsp;GB of HDD/SSD space
```

1. Install Git: <https://git-scm.com/download/win>.

2. Install Python 3.8 or newer.

3. If you plan to use the FMOD sound library, also install FMOD Studio SDK
   2.02.15.

4. Create a project directory at the root of any drive.

   ```{note}
   The directory name should not contain spaces or non-Latin characters.
   ```

   ```text
   md X:\develop
   cd X:\develop
   ```

5. Clone the Dagor Engine source code:

   ```text
   git clone https://github.com/Prose-Studio/DagorEngine.git
   cd DagorEngine
   ```

6. Run `dng.py devtools`.

   It downloads, installs, and configures the build toolkit. Provide the path to
   the build toolkit directory as an argument; it creates the directory if it
   doesn't exist and skips what is already set up when run again.

   ```text
   python dng.py devtools X:\develop\devtools
   ```

   ```{important}
   - If the script is not run as an administrator, installers of certain
     programs may request permission for installation, which you should grant.
   - If you plan to use plugins for 3ds Max, press `Y` when the script asks if
     you want to install the 3ds Max SDK.
   - The script will also ask to add the path `X:\develop\devtools` to the
     `PATH` environment variable and set the `GDEVTOOL` variable to point to
     this directory.
   ```

   After the script completes its work, the `X:\develop\devtools` directory
   holds the compilers (LLVM, MSVC), the Windows SDKs, the SDKs of the graphics
   drivers (DXC, Agility SDK, AGS, nvapi, Nsight Aftermath, Streamline,
   FidelityFX), OpenXR, astcenc, ispc, nasm, ducible and `jam.exe`, the build
   tool used instead of Make.

7. Restart the command line console to make the new environment variables
   available.

## How to Build: Build from Source Code

Run `python dng.py build` in `DagorEngine` to build the engine toolkit, dargbox
and the project template from the source code (`python dng.py build -h` lists
the projects and options). This process may take a considerable amount of
time.

The data the tools load at runtime and that is not built (the editors'
`commonData`, dargbox's fonts and UI) is part of the repository, in
`prog/tools/toolsData`; the build copies it into `tools/`.

To start a game of your own, see [Creating a Project](new_project.md).

## Samples

The assets of the samples are not in the repository: they are Gaijin's
downloads under Gaijin's non-commercial content license (see
`outerSpace/LICENSE.txt`), listed in the `README.md` of the engine. Unpack the
ones you want into `DagorEngine` and name the samples to build them, for
example `python dng.py build testGI`; `python dng.py build --list` shows whose
content is unpacked.

```text
develop
└── DagorEngine
    ├── prog
    ├── samples
    │   ├── skiesSample
    │   │   ├── game
    │   │   ├── develop
    │   │   └── prog
    │   └── testGI
    │       ├── game
    │       ├── develop
    │       └── prog
    ├── tools
    └── _docs
```

where

- `prog`: contains game source code.
- `develop`: contains initial assets.
- `game`: directory where assets are placed after building and game executable
  files are located.

  ```{seealso}
  For more information, see
  [Directory Structure Overview](directory_structure.md).
  ```

