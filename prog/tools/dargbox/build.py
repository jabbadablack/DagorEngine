#!/usr/bin/env python3
import sys
sys.path.append('../../..')
from pathlib import Path
sys.path.insert(0, str(next(p for p in Path(__file__).resolve().parents if (p / 'prog/_jBuild/bootstrap/build_all.py').exists()) / 'prog/_jBuild/bootstrap'))
from build_all import run, run_per_platform, VROMFS_PACKER_EXE, BUILD_COMPONENTS, DAGOR_HOST, JAM_BUILD_TARGET_ARCH_OPTIONS
sys.path.pop()


# build EXE
if 'code' in BUILD_COMPONENTS:
  run(['jam', '-sRoot=../..', '-f', 'dargbox/jamfile'] + JAM_BUILD_TARGET_ARCH_OPTIONS, cwd='..')

# build shaders
if 'shaders' in BUILD_COMPONENTS:
  run_per_platform(
    cmds_windows = ['compile_shaders_dx11.bat', 'compile_shaders_dx12.bat',
                    'compile_shaders_metal.bat', 'compile_shaders_spirV.bat'],
    cmds_macOS   = ['./compile_shaders_metal.sh'],
    cmds_linux   = ['./compile_shaders_spirv.sh'],
    cwd='./shaders')

#build vromfs
if 'vromfs' in BUILD_COMPONENTS:
  run([VROMFS_PACKER_EXE, 'darg.vromfs.blk', '-platform:PC', '-quiet'], cwd='.')
