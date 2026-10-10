# Tools data

Data the engine tools load at runtime that is not built from source: the editors' `commonData` (icons, fonts, themes,
brushes, environment lighting, editor textures and settings), the blkEditor's Scintilla/Lexilla DLLs, the 3ds Max
plugin settings and dargbox's fonts, UI, sounds and launchers.

`dng.py build` copies this directory into `tools/` (the same layout: `dagor_cdk/commonData` goes to
`tools/dagor_cdk/commonData`, `dargbox` to `tools/dargbox`, ...). A file is copied when it is missing in `tools/` or the
one here is newer, so local edits in `tools/` (e.g. `tools/dargbox/settings.blk`) stay until this copy changes; nothing
in `tools/` is deleted. Edit the files here, not in `tools/`.

The files are stored byte for byte (`-text` in `.gitattributes`): line endings are never converted.

It started as Gaijin's `tools-base.7z` (head-2026.09.20), without the DXC DLLs, which `prog/tools/ShaderCompiler2`
copies from the devtools, and the GUI shader dumps of commonData, which the engine tools build compiles.

## Fonts

| Font | Files | License |
|---|---|---|
| Noto Sans, Noto Sans CJK JP, Noto Sans Symbols, Noto Sans Symbols 2 | `dargbox/fonts/Noto*` | SIL Open Font License 1.1 |
| Roboto | `dagor_cdk/commonData/fonts/roboto-*.ttf` | Apache License 2.0 |
| DejaVu Sans | `dagor_cdk/commonData/fonts/dejaVuSans.ttf` | Bitstream Vera / DejaVu fonts license |
| JetBrains Mono | `*/fonts/jetbrains-mono-nl-regular.ttf` | SIL Open Font License 1.1 |
| Fira Sans | `dargbox/fonts/firasans-medium.ttf` | SIL Open Font License 1.1 |
| Lato | `dargbox/fonts/lato-regular.ttf` | SIL Open Font License 1.1 |
| Font Awesome 4 | `dargbox/fonts/fontawesome-webfont.ttf` | SIL Open Font License 1.1 |

The license texts are in `LICENSES/` (copied to `tools/LICENSES`), the copyright notices in the font files.
