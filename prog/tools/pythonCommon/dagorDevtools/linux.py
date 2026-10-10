"""dng.py devtools on Linux: the distro's compiler and library packages, FMOD, DXC, astcenc, ispc."""
import glob
import os
import pathlib
import platform
import re
import shutil

from .common import FMOD, run

linux_release_name = ''
linux_release_id = ''
linux_release_ver = ''
linux_arch_type = platform.uname().machine

with open('/etc/os-release', 'r') as file:
  for val_pair in re.findall(r'(\w+)=(.+)\n', file.read()):
    if val_pair[0] == 'NAME':
      linux_release_name = val_pair[1]
    elif val_pair[0] == 'ID':
      linux_release_id = val_pair[1]
    elif val_pair[0] == 'VERSION':
      linux_release_ver = val_pair[1]

is_rosa_linux = (linux_release_id == 'rosa')
is_astra_linux = "Astra Linux" in linux_release_name
is_ubuntu = ("Ubuntu" in linux_release_name)
is_centos = ('centos' in linux_release_id)
is_altlinux = (linux_release_id == 'altlinux')
is_elbrus_linux = ('elbrus' in linux_release_id)


def install_packages():
  pkg_to_install = ['nasm']
  pkg_install_cmd = ''
  if is_rosa_linux:
    pkg_install_cmd = 'dnf install'
    pkg_to_install += ['python3-pip', 'gcc', 'gcc-c++', 'clang', 'lib64ubsan-devel']
    pkg_to_install += ['lib64x11-devel', 'lib64xrandr-devel', 'lib64fltk-devel', 'lib64xkbfile-devel', 'lib64udev-devel', 'lib64pulseaudio-devel', 'lib64alsa-oss-devel']
  elif is_altlinux:
    pkg_install_cmd = 'apt-get install'
    pkg_to_install += ['python3-module-pip', 'clang21.1', 'libclang21', 'libasan-devel-static']
    pkg_to_install += ['libX11-devel', 'libXrandr-devel', 'libXcursor-devel', 'libfltk-devel', 'libxkbfile-devel', 'libxkbcommon-devel',
                       'libudev-devel', 'libpulseaudio-devel', 'libalsa-devel', 'libuuid-devel', 'libdbus-devel']
  elif is_elbrus_linux:
    pkg_install_cmd = 'apt install'
    pkg_to_install  = ['python3-pip']
    pkg_to_install += ['libx11', 'libxrandr', 'fltk', 'libxkbfile', 'pulseaudio', 'alsa-lib', 'uuid']
  elif is_ubuntu:
    pkg_install_cmd = 'apt install'
    pkg_to_install += ['python3-pip', 'gcc', 'clang']
    pkg_to_install += ['libx11-dev', 'libxrandr-dev', 'libxcursor-dev', 'libxkbcommon-dev', 'libfltk1.3-dev', 'libxkbfile-dev', 'libudev-dev', 'libpulse-dev', 'uuid-dev']
  elif is_astra_linux:
    pkg_install_cmd = 'apt install'
    pkg_to_install += ['python3-pip', 'gcc-mozilla', 'clang-10']
    pkg_to_install += ['libx11-dev', 'libxrandr-dev', 'libxcursor-dev', 'libxkbcommon-dev', 'libfltk1.3-dev', 'libxkbfile-dev', 'libudev-dev', 'libpulse-dev', 'uuid-dev']
  elif is_centos:
    pkg_install_cmd = 'yum install'
    pkg_to_install += ['python3-pip', 'devtoolset-11', 'llvm-toolset-7.0']
    pkg_to_install += ['libX11-devel', 'libXrandr-devel', 'libfltk-devel', 'libxkbfile-devel', 'libgudev1-devel', 'pulseaudio-libs-devel', 'alsa-lib-devel']
  else:
    pkg_to_install += ['python3-pip', 'gcc', 'gcc-c++', 'clang']
    pkg_to_install += ['libx11-dev', 'libxrandr-dev', 'libxcursor-dev', 'libxkbcommon-dev', 'libfltk1.3-dev', 'libxkbfile-dev', 'libudev-dev', 'libpulse-dev', 'libalsa-devel']

  if pkg_install_cmd != '':
    print('--- will try to install required packages:\n  '+' '.join(pkg_to_install))
    run('sudo {0} {1}'.format(pkg_install_cmd, ' '.join(pkg_to_install)))
  else:
    print('NOTE: you have to install these (or similar) packages manually:\n  ' + ' '.join(pkg_to_install) + '\n\n')

  if is_rosa_linux:
    if not pathlib.Path('/usr/lib64/libclang.so').exists() and pathlib.Path('/usr/lib64/libclang.so.12').exists():
      run('sudo ln -s libclang.so.12 /usr/lib64/libclang.so')


def setup_fmod(d):
  fmod_dest_folder = d.path(FMOD)
  if pathlib.Path(fmod_dest_folder).exists():
    print('=== FMOD symlinks found at {0}, skipping setup'.format(fmod_dest_folder))
    return
  for fmod_src_folder in glob.glob('{0}/fmodstudioapi2*linux'.format(os.environ['HOME'])):
    if pathlib.Path(fmod_src_folder+'/api').exists():
      print('+++ FMOD found at {0}'.format(fmod_src_folder))
      for api in ['core', 'studio']:
        pathlib.Path(fmod_dest_folder+'/'+api+'/linux64').mkdir(parents=True, exist_ok=True)
        d.link_dir(fmod_src_folder+'/api/'+api+'/inc', fmod_dest_folder+'/'+api+'/linux64/inc')
        d.link_dir(fmod_src_folder+'/api/'+api+'/lib', fmod_dest_folder+'/'+api+'/linux64/lib')
      shutil.copyfile(fmod_src_folder+'/doc/LICENSE.TXT', fmod_dest_folder+'/LICENSE.TXT')
      shutil.copyfile(fmod_src_folder+'/doc/revision.txt', fmod_dest_folder+'/revision.txt')
      return
  print('--- FMOD not found, creating stub folders')
  print('consider downloading and installing https://www.fmod.com/download#fmodengine - Linux Download')
  pathlib.Path(fmod_dest_folder+'/core/linux64/inc').mkdir(parents=True, exist_ok=True)
  pathlib.Path(fmod_dest_folder+'/studio/linux64/inc').mkdir(parents=True, exist_ok=True)


def setup_dxc(d):
  dxc_dest_folder = d.path('DXC-1.8.2505.1')
  if pathlib.Path(dxc_dest_folder).exists():
    print('=== DXC May 2025 - Patch 1 -- 1.8.2505.1 found at {0}, skipping setup'.format(dxc_dest_folder))
    return
  d.unpack(d.download('https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.8.2505.1/'
                      'linux_dxc_2025_07_14.x86_64.tar.gz'), dxc_dest_folder)
  pathlib.Path(dxc_dest_folder+'/lib/linux64').mkdir(parents=True, exist_ok=True)
  d.link_dir(dxc_dest_folder+'/lib/libdxcompiler.so', dxc_dest_folder+'/lib/linux64/libdxcompiler.so')
  print('+++ DXC May 2025 - Patch 1 -- 1.8.2505.1 installed at {0}'.format(dxc_dest_folder))
  if linux_arch_type == 'e2k':
    print('!!! arch={0} differs from x86_64, you should rebuild {1} for\n'
          '    your arch and place result binary to {2}/lib/linux64/libdxcompiler.so\n\n'
          .format(linux_arch_type, 'https://github.com/microsoft/DirectXShaderCompiler', dxc_dest_folder))


def setup(d):
  print('Detected linux: {0} {1}  ({2}) arch={3}'.format(linux_release_name, linux_release_ver, linux_release_id, linux_arch_type))
  install_packages()
  d.link_python()
  setup_fmod(d)
  setup_dxc(d)

  if linux_arch_type == 'e2k':  # no prebuilt astcenc and ispc
    if not d.exists('astcenc-4.6.1'):
      pathlib.Path(d.path('astcenc-4.6.1/linux64')).mkdir(parents=True, exist_ok=True)
      print('+++ ASTC encoder 4.6.1 folder created at {0}'.format(d.path('astcenc-4.6.1')))
      print('!!! arch={0} differs from x86_64, you should rebuild {1}\n'
            '    for your arch and place result binary to {2}/linux64/astcenc-native\n\n'
            .format(linux_arch_type, 'https://github.com/ARM-software/astc-encoder', d.path('astcenc-4.6.1')))
    if not d.exists('ispc-v1.23.0-linux'):
      pathlib.Path(d.path('ispc-v1.23.0-linux')).mkdir(parents=True, exist_ok=True)
      print('+++ ISPC v1.23.0 skipped (stub created at {0})'.format(d.path('ispc-v1.23.0-linux')))
      print('!!! arch={0} differs from x86_64, you should rebuild {1}\n'
            '    for your arch and place result binary to {2}/bin/ispc\n\n'
            .format(linux_arch_type, 'https://github.com/ispc/ispc', d.path('ispc-v1.23.0-linux')))
  else:
    d.install_astcenc('astcenc-4.6.1-linux-x64.zip', 'linux64')
    d.install_ispc('ispc-v1.23.0-linux-oneapi.tar.gz', 'ispc-v1.23.0-linux')

  jam = 'jam-centOS-7-x86_64.tar.gz'
  if linux_arch_type == 'e2k':
    if is_altlinux:
      jam = 'jam-AltLinux-10-e2k-v3.tar.gz'
    elif is_elbrus_linux:
      jam = 'jam-ElbrusLinux-8-e2k-v3.tar.gz'
  d.install_jam(jam)

  extra = []
  if linux_arch_type == 'e2k':
    extra += ['PlatformArch = e2k ;', 'PlatformSpec ?= clang ;', 'WError = no ;',
              'RemoveCompilerSwitches_linux/gcc = -mno-recip -minline-all-stringops -fconserve-space ;']
  if is_astra_linux:
    extra += ['PlatformSpec = clang ;']
  if is_astra_linux or is_rosa_linux:
    extra += ['MArch = -default- ; #remove it to build for haswell'] # to avoid building daNetGame for haswell arch
  return extra


def finish(d):
  return False
