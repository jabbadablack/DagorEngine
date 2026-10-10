#!/usr/bin/env python3
# builds physTest: python build.py [code] [shaders] [arch:<arch>] [--dry-run] (all when none is given)
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '../../tools')
from pythonCommon import dagorBuild  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders'])

# build EXE
if 'code' in b.components:
  b.run(['jam', '-f', 'jamfile-test-bullet'] + b.jam_arch)
  b.run(['jam', '-f', 'jamfile-test-jolt'] + b.jam_arch)

# build shaders
if 'shaders' in b.components:
  b.run_per_platform(
    windows = ['compile_game_shaders-dx11.bat', 'compile_game_shaders-metal.bat', 'compile_game_shaders-spirv.bat'],
    macOS   = ['./compile_shaders_metal.sh'],
    linux   = ['./compile_shaders_spirv.sh'],
    cwd='./shaders')

sys.exit(b.exit_code)
