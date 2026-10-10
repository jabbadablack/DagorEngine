"""dng.py devtools on macOS: nasm, FMOD, DXC, astcenc, ispc and the devtools mac folder."""
import os
import pathlib
import platform
import shutil

from ..dagorBuild import ENGINE_ROOT
from .common import FMOD, run


def setup_nasm(d):
  nasm_dest_folder = d.path('nasm')
  if pathlib.Path(nasm_dest_folder).exists():
    print('=== NASM symlink found at {0}, skipping setup'.format(nasm_dest_folder))
    return
  d.unpack(d.download('https://www.nasm.us/pub/nasm/releasebuilds/2.16/macosx/nasm-2.16-macosx.zip'), d.dest)
  run('chmod 755 '+d.path('nasm-2.16/nasm'))
  run('chmod 755 '+d.path('nasm-2.16/ndisasm'))
  print('--- will copy nasm to /usr/local/bin using sudo:')
  run('sudo cp '+d.path('nasm-2.16/nasm')+' /usr/local/bin/nasm')
  print('+++ NASM 2.16 installed at {0}'.format(nasm_dest_folder))


def setup_fmod(d):
  fmod_dest_folder = d.path(FMOD)
  if pathlib.Path(fmod_dest_folder).exists():
    print('=== FMOD symlinks found at {0}, skipping setup'.format(fmod_dest_folder))
    return
  fmod_src_folder = '{0}/FMOD Programmers API'.format(os.environ['HOME'])
  if pathlib.Path(fmod_src_folder).exists():
    print('+++ FMOD found at {0}'.format(fmod_src_folder))
    for api in ['core', 'studio']:
      pathlib.Path(fmod_dest_folder+'/'+api+'/macosx').mkdir(parents=True, exist_ok=True)
      d.link_dir(fmod_src_folder+'/api/'+api+'/inc', fmod_dest_folder+'/'+api+'/macosx/inc')
      d.link_dir(fmod_src_folder+'/api/'+api+'/lib', fmod_dest_folder+'/'+api+'/macosx/lib')
    shutil.copyfile(fmod_src_folder+'/doc/LICENSE.TXT', fmod_dest_folder+'/LICENSE.TXT')
    shutil.copyfile(fmod_src_folder+'/doc/revision.txt', fmod_dest_folder+'/revision.txt')
  else:
    print('--- FMOD not found at {0}, creating stub folders'.format(fmod_src_folder))
    print('consider downloading and installing https://www.fmod.com/download#fmodengine - Mac Download')
    pathlib.Path(fmod_dest_folder+'/core/macosx/inc').mkdir(parents=True, exist_ok=True)
    pathlib.Path(fmod_dest_folder+'/studio/macosx/inc').mkdir(parents=True, exist_ok=True)


def setup_dxc(d):
  dxc_dest_folder = d.path('DXC-1.8.2505.1')
  if pathlib.Path(dxc_dest_folder).exists():
    print('=== DXC May 2025 - Patch 1 -- 1.8.2505.1 found at {0}, skipping setup'.format(dxc_dest_folder))
    return
  d.unpack(d.download('https://github.com/Prose-Studio/DagorEngine/releases/download/dxc-1.8.2505.1/DXC-1.8.2505.1.tar.gz'), d.dest)
  for other in ['linux64', 'win64', 'win-arm64']:
    shutil.rmtree(dxc_dest_folder+'/lib/'+other)
  print('+++ DXC May 2025 - Patch 1 -- 1.8.2505.1 installed at {0}'.format(dxc_dest_folder))


def setup(d):
  d.link_python()
  setup_nasm(d)
  setup_fmod(d)
  setup_dxc(d)
  d.install_astcenc('astcenc-4.6.1-macos-universal.zip', 'macosx')
  d.install_ispc('ispc-v1.23.0-macOS.universal.tar.gz', 'ispc-v1.23.0-macOS.x86_64')
  d.install_jam('jam-macOS-11.0-arm64.tar.gz' if platform.processor() == 'arm' else 'jam-macOS-10.9-x64_86.tar.gz')
  return []


def finish(d):
  print('--- will prepare {0}/mac folder using jamfile:'.format(d.dest))
  run('sudo jam -sRoot=. -f prog/engine/kernel/jamfile mkdevtools', cwd=ENGINE_ROOT)
  return False
