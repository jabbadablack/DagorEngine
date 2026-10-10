#!/usr/bin/env python3
# builds Outer Space: python build.py [code] [shaders] [vromfs] [assets] [gui] [arch:<arch>] [--dry-run] (all when none is given)
import os
import shutil
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '../../prog/tools')
from pythonCommon import dagorBuild  # noqa: E402
from pythonCommon.dagorBuild import HOST, HOST_ARCH, VROMFS_PACKER  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders', 'vromfs', 'assets', 'gui'])

# build EXE
if 'code' in b.components:
  AOT_COMPILER_JAM_OPTIONS = []
  PROJ_JAM_OPTIONS = b.jam_arch
  if b.arch != '':
    if HOST == 'macOS' and b.arch == 'arm64': # macOS can run both x86_64 and arm64
      AOT_COMPILER_JAM_OPTIONS += b.jam_arch
    elif HOST == 'windows' and b.arch == 'arm64' and HOST_ARCH != b.arch:
      AOT_COMPILER_JAM_OPTIONS += ['-sPlatformArch=x86_64']
    else: # otherwise just use the same arch to match main project settings
      AOT_COMPILER_JAM_OPTIONS = PROJ_JAM_OPTIONS
  elif HOST == 'windows': # use HOST_ARCH as default for windows
    PROJ_JAM_OPTIONS = ['-sPlatformArch='+HOST_ARCH]
    AOT_COMPILER_JAM_OPTIONS = PROJ_JAM_OPTIONS

  b.run(['jam', '-sRoot=../..', '-sProjectLocation=outerSpace/prog', '-sTarget=outer_space-aot', '-sOutDir=../tools/das-aot',
         '-f', '../../prog/daNetGame-das-aot/jamfile'] + AOT_COMPILER_JAM_OPTIONS)
  b.run(['jam', '-sNeedDasAotCompile=yes'] + PROJ_JAM_OPTIONS)
  b.run(['jam', '-sNeedDasAotCompile=yes', '-sDedicated=yes'] + PROJ_JAM_OPTIONS)
  if HOST == 'windows':
    b.run(['jam', '-sNeedDasAotCompile=yes', '-sDedicated=yes', '-sTargetType=dll'] + PROJ_JAM_OPTIONS)

  b.run(['jam', '-sProjectPath=outerSpace', '-sRoot=../..', '-f', '../../prog/tools/relay/jamfile'] + PROJ_JAM_OPTIONS)

  b.run(['jam', '-f', 'jamfile-decrypt'] + PROJ_JAM_OPTIONS)

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

if 'vromfs' in b.components:
  #build game vromfs
  b.run([VROMFS_PACKER, 'mk.vromfs.blk', '-quiet', '-addpath:.'], cwd='.')

  #build vromfs for dev-launcher
  b.run([VROMFS_PACKER, 'common.vromfs.blk', '-platform:PC', '-quiet', '-addpath:.'], cwd='utils/dev_launcher')

# dabuild assets
if 'assets' in b.components:
  b.run(dagorBuild.DABUILD_CMD + ['../application.blk'], cwd='../develop')

# build UI data (fonts, atlas, vromfs)
if 'gui' in b.components:
  if not b.dry_run:
    shutil.rmtree('../develop/gui/pc.out.ui', ignore_errors=True)
    os.makedirs('../develop/gui/pc.out.ui')
  b.run([dagorBuild.FONTGEN, 'fontgenPC.blk', '-fullDynamic', '-quiet'], cwd='../develop/gui/fonts')
  b.run([VROMFS_PACKER, 'skin.vromfs.blk', '-quiet'], cwd='../develop/gui')
  b.run([VROMFS_PACKER, 'fonts.vromfs.blk', '-quiet'], cwd='../develop/gui')

if 'shaders' in b.components and 'vromfs' in b.components:
  b.run([sys.executable, './update_snapshot.py', '--no-cvs-update'], cwd='./tools')

sys.exit(b.exit_code)
