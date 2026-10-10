#!/usr/bin/env python3
# builds dngSceneViewer: python build.py [code] [shaders] [vromfs] [arch:<arch>] [--dry-run] (all when none is given)
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '../../../prog/tools')
from pythonCommon import dagorBuild  # noqa: E402
from pythonCommon.dagorBuild import HOST, HOST_ARCH  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders', 'vromfs'])

# build EXE
if 'code' in b.components:
  AOT_COMPILER_JAM_OPTIONS = []
  if b.arch != '':
    if HOST == 'macOS' and b.arch == 'arm64': # macOS can run both x86_64 and arm64
      AOT_COMPILER_JAM_OPTIONS += b.jam_arch
    elif HOST == 'windows' and b.arch == 'arm64' and HOST_ARCH != b.arch:
      AOT_COMPILER_JAM_OPTIONS += ['-sPlatformArch=x86_64']
    else: # otherwise just use the same arch to match main project settings
      AOT_COMPILER_JAM_OPTIONS = b.jam_arch

  b.run(['jam'] + AOT_COMPILER_JAM_OPTIONS, cwd='./_aot')
  b.run(['jam', '-sNeedDasAotCompile=yes'] + b.jam_arch)

# build shaders
if 'shaders' in b.components:
  b.run_per_platform(
    windows = ['compile_shaders_dx12.bat', 'compile_shaders_dx11.bat',
               'compile_shaders_metal.bat', 'compile_shaders_spirv.bat',
               'compile_shaders_tools.bat', 'compile_shaders_exp.bat',
               'compile_shaders_impostorbaker.bat'],
    macOS   = ['./compile_shaders_metal.sh', './compile_tool_shaders_metal.sh'],
    linux   = ['./compile_shaders_spirv.sh', './compile_tool_shaders_spirv.sh'],
    cwd='./shaders')

#build vromfs
if 'vromfs' in b.components:
  b.run([dagorBuild.VROMFS_PACKER, 'prog.vromfs.blk', '-platform:PC', '-quiet', '-addpath:.'])

sys.exit(b.exit_code)
