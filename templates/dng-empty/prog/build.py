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
dagorProject, PROJECT = project.load()  # puts the engine's prog/tools on sys.path
from pythonCommon import dagorBuild  # noqa: E402
from pythonCommon.dagorBuild import HOST, HOST_ARCH, tool  # noqa: E402

b = dagorBuild.parse(sys.argv[1:], ['code', 'shaders', 'vromfs', 'tools', 'assets'])
if 'shaders' in b.components and 'vromfs' in b.components and 'tools' not in b.components:
  b.components.append('tools')  # the editor snapshot is made of both

os.chdir(PROG_DIR)
if not b.dry_run:
  dagorProject.setup(PROJECT)  # the generated engine glue is current before anything is built

if 'code' in b.components:
  JAM = ['jam', '-sNeedDasAotCompile=yes'] + b.jam_arch
  if HOST == 'windows' and not b.arch:
    JAM += ['-sPlatformArch=' + HOST_ARCH]
  b.run(JAM)
  b.run(JAM + ['-sDedicated=yes'])

if 'shaders' in b.components:
  # outputs: ../game/compiledShaders (game), ../tools (daEditor, daViewer, dabuild, impostorBaker); intermediate files
  # go to <project>/_output/shaders. dx11 is the default windows driver and what daEditor renders levels with.
  OUT = '../../_output/shaders/' + PROJECT.codename
  DSC = ['-q', '-shaderOn', '-nodisassembly', '-commentPP', '-codeDumpErr', '-maxVSF', '4096']
  EXP = ['-q', '-shaderOn', '-no_sha1_cache', '-clearBlkHashInDump']  # dabuild only needs the shader descriptions
  b.run_per_platform(
    windows=[[tool('dsc2-hlsl11-dev'), 'shaders_dx11.blk'] + DSC + ['-o', OUT + '-game~dx11'],
             [tool('dsc2-dx12-dev'), 'shaders_dx12.blk'] + DSC + ['-wx', '-o', OUT + '-game~dx12'],
             [tool('dsc2-hlsl11-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~dx11'],
             [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
             [tool('dsc2-dx12-dev'), 'shaders_impostorbaker.blk'] + DSC + ['-o', OUT + '-impostorbaker~dx12']],
    macOS=[[tool('dsc2-metal-dev'), 'shaders_metal.blk'] + DSC + ['-o', OUT + '-game~metal'],
           [tool('dsc2-metal-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~metal', '-out', '../../tools/toolsMTL'],
           [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
           [tool('dsc2-metal-dev'), 'shaders_impostorbaker.blk'] + DSC +
           ['-o', OUT + '-impostorbaker~metal', '-out', '../../tools/tools.impostorbakerMTL']],
    linux=[[tool('dsc2-spirv-dev'), 'shaders_spirv.blk'] + DSC + ['-o', OUT + '-game~spirv'],
           [tool('dsc2-spirv-dev'), 'shaders_tools11.blk'] + DSC + ['-o', OUT + '-tools~spirv', '-out', '../../tools/toolsSpirV'],
           [tool('dsc2-stub-dev'), 'shaders_tools_exp.blk'] + EXP + ['-o', OUT + '~exp'],
           [tool('dsc2-spirv-dev'), 'shaders_impostorbaker.blk'] + DSC +
           ['-o', OUT + '-impostorbaker~spirv', '-out', '../../tools/tools.impostorbakerSpirV']],
    cwd='shaders')

if 'vromfs' in b.components:
  b.run([dagorBuild.VROMFS_PACKER, 'prog.vromfs.blk', '-platform:PC', '-quiet', '-addpath:.'])

if 'tools' in b.components and not b.dry_run:
  from update_dng_snapshots import update_dng_snapshot  # noqa: E402  prog/tools is on sys.path
  print('--- Updating the daEditor snapshot', flush=True)
  update_dng_snapshot(PROJECT.root, 'game', glob.glob(PROJECT.root + '/game/*.vromfs.bin'), skip_cvs_update=True)
  os.chdir(PROG_DIR)  # update_dng_snapshot changes the cwd

if 'assets' in b.components:
  b.run(dagorBuild.DABUILD_CMD + ['../application.blk'], cwd='../develop')

sys.exit(b.exit_code)
