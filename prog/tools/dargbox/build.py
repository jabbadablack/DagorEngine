#!/usr/bin/env python3
# builds dargbox: python build.py [code] [shaders] [vromfs] [arch:<arch>] [--dry-run] (all when none is given)
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '..')
from pythonCommon import dagorBuild  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders', 'vromfs'])

# build EXE
if 'code' in b.components:
  b.run(['jam', '-sRoot=../..', '-f', 'dargbox/jamfile'] + b.jam_arch, cwd='..')

# build shaders
if 'shaders' in b.components:
  b.run_per_platform(
    windows = ['compile_shaders_dx11.bat', 'compile_shaders_dx12.bat',
               'compile_shaders_metal.bat', 'compile_shaders_spirV.bat'],
    macOS   = ['./compile_shaders_metal.sh'],
    linux   = ['./compile_shaders_spirv.sh'],
    cwd='./shaders')

#build vromfs
if 'vromfs' in b.components:
  b.run([dagorBuild.VROMFS_PACKER, 'darg.vromfs.blk', '-platform:PC', '-quiet'], cwd='.')

sys.exit(b.exit_code)
