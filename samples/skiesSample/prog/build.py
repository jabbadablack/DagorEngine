#!/usr/bin/env python3
# builds skiesSample: python build.py [code] [shaders] [assets] [arch:<arch>] [--dry-run] (all when none is given)
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '../../../prog/tools')
from pythonCommon import dagorBuild  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders', 'assets'])

# build EXE
if 'code' in b.components:
  b.run(['jam'] + b.jam_arch)

# build shaders
if 'shaders' in b.components:
  b.run_per_platform(
    windows = ['compile_shaders_dx12.bat', 'compile_shaders_dx11.bat', 'compile_shaders_metal.bat', 'compile_shaders_spirv.bat',
               'compile_shaders_tools.bat'],
    macOS   = ['./compile_shaders_metal.sh', './compile_tool_shaders_metal.sh'],
    linux   = ['./compile_shaders_spirv.sh', './compile_tool_shaders_spirv.sh'],
    cwd='./shaders')

# dabuild assets
if 'assets' in b.components:
  b.run(dagorBuild.DABUILD_CMD + ['../application.blk'], cwd='../develop')

sys.exit(b.exit_code)
