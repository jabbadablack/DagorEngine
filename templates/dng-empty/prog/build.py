#!/usr/bin/env python3
"""Builds the game: python build.py [code] [shaders] [vromfs] [tools] [assets] [arch:<arch>] [--dry-run]
(all of them when none is given, in this order).

  code     the client and the dedicated server (with their das AOT compiler) into ../game/<platform>-<arch>
  shaders  the game shaders into ../game/compiledShaders, the tool shaders into ../tools
  vromfs   prog.vromfs.blk into ../game/dng_empty.vromfs.bin
  tools    the snapshot of shaders, vromfs and tools/*.das daEditor renders levels with (../tools/snapshot)
  assets   develop/assets with dabuild into ../game/content
"""
import glob
import os
import sys

PROG_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(PROG_DIR))
import project  # noqa: E402  ../project.py: the engine named by ../engine.blk
sys.path.pop(0)
dagorProject, PROJECT = project.load()

sys.path.insert(0, project.engine_root())
from build_all import (BUILD_TARGET_ARCH, DABUILD_CMD, DAGOR_HOST, DAGOR_HOST_ARCH, DAGOR_TOOLS_FOLDER,  # noqa: E402
                       JAM_BUILD_TARGET_ARCH_OPTIONS, VROMFS_PACKER_EXE, run, run_per_platform)
sys.path.pop(0)

ALL_COMPONENTS = ['code', 'shaders', 'vromfs', 'tools', 'assets']
COMPONENTS = [a for a in sys.argv[1:] if not a.startswith(('arch:', 'project:', '-'))] or ALL_COMPONENTS
for c in COMPONENTS:
  if c not in ALL_COMPONENTS + ['gui']:  # gui: a build_all.py component, nothing to build here (no fonts or UI packs)
    sys.exit('unknown component "{}": expected {}'.format(c, ', '.join(ALL_COMPONENTS)))
if 'shaders' in COMPONENTS and 'vromfs' in COMPONENTS and 'tools' not in COMPONENTS:
  COMPONENTS.append('tools')  # the editor snapshot is made of both


def tool(name):
  return os.path.join(DAGOR_TOOLS_FOLDER, name + ('.exe' if DAGOR_HOST == 'windows' else ''))


os.chdir(PROG_DIR)
dagorProject.setup(PROJECT)  # the generated engine glue is current before anything is built
ok = True

if 'code' in COMPONENTS:
  JAM = ['jam', '-sNeedDasAotCompile=yes'] + JAM_BUILD_TARGET_ARCH_OPTIONS
  if DAGOR_HOST == 'windows' and BUILD_TARGET_ARCH == '':
    JAM += ['-sPlatformArch=' + DAGOR_HOST_ARCH]
  ok = run(JAM) and ok
  ok = run(JAM + ['-sDedicated=yes']) and ok

if 'shaders' in COMPONENTS:
  # outputs: ../game/compiledShaders (game), ../tools (daEditor, daViewer, dabuild, impostorBaker); intermediate files
  # go to <project>/_output/shaders. dx11 is the default windows driver and what daEditor renders levels with.
  OUT = '../../_output/shaders/' + PROJECT.codename
  DSC = ['-q', '-shaderOn', '-nodisassembly', '-commentPP', '-codeDumpErr', '-maxVSF', '4096']
  EXP = ['-q', '-shaderOn', '-no_sha1_cache', '-clearBlkHashInDump']  # dabuild only needs the shader descriptions
  ok = run_per_platform(
    cmds_windows=[[tool('dsc2-hlsl11-dev'), 'shaders_dx11.blk'] + DSC + ['-o', OUT + '-game~dx11'],
                  [tool('dsc2-dx12-dev'), 'shaders_dx12.blk'] + DSC + ['-wx', '-o', OUT + '-game~dx12'],
                  [tool('dsc2-hlsl11-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~dx11'],
                  [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
                  [tool('dsc2-dx12-dev'), 'shaders_impostorbaker.blk'] + DSC + ['-o', OUT + '-impostorbaker~dx12']],
    cmds_macOS=[[tool('dsc2-metal-dev'), 'shaders_metal.blk'] + DSC + ['-o', OUT + '-game~metal'],
                [tool('dsc2-metal-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~metal', '-out', '../../tools/toolsMTL'],
                [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
                [tool('dsc2-metal-dev'), 'shaders_impostorbaker.blk'] + DSC +
                ['-o', OUT + '-impostorbaker~metal', '-out', '../../tools/tools.impostorbakerMTL']],
    cmds_linux=[[tool('dsc2-spirv-dev'), 'shaders_spirv.blk'] + DSC + ['-o', OUT + '-game~spirv'],
                [tool('dsc2-spirv-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~spirv', '-out', '../../tools/toolsSpirV'],
                [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
                [tool('dsc2-spirv-dev'), 'shaders_impostorbaker.blk'] + DSC +
                ['-o', OUT + '-impostorbaker~spirv', '-out', '../../tools/tools.impostorbakerSpirV']],
    cwd='shaders') and ok

if 'vromfs' in COMPONENTS:
  ok = run([VROMFS_PACKER_EXE, 'prog.vromfs.blk', '-platform:PC', '-quiet', '-addpath:.']) and ok

if 'tools' in COMPONENTS:
  sys.path.insert(0, os.path.join(project.engine_root(), 'prog', 'tools'))
  from update_dng_snapshots import update_dng_snapshot  # noqa: E402
  sys.path.pop(0)
  print('--- Updating the daEditor snapshot', flush=True)
  update_dng_snapshot(PROJECT.root, 'game', glob.glob(PROJECT.root + '/game/*.vromfs.bin'), skip_cvs_update=True)
  os.chdir(PROG_DIR)  # update_dng_snapshot changes the cwd

if 'assets' in COMPONENTS:
  ok = run(DABUILD_CMD + ['../application.blk'], cwd='../develop') and ok

sys.exit(0 if ok else 1)
