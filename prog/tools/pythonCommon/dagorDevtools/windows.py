"""dng.py devtools on Windows: Visual Studio, Windows SDKs, LLVM and the SDKs of the PC drivers."""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import zipfile

from ..dagorBuild import HOST_ARCH
from .common import FMOD, ask, error, pip_install, run


def setup_python(d):
  python_dest_folder = d.path('python3')
  python_src_folder = os.path.dirname(sys.executable)
  if not pathlib.Path(python_src_folder+'/python.exe').exists():
    python_src_folder = os.environ.get('LOCALAPPDATA', '') + '/Programs/Python'
  if pathlib.Path(python_src_folder).exists():
    if not pathlib.Path(python_src_folder+'/python.exe').exists():
      for item in pathlib.Path(python_src_folder).glob("Python3*"):
        if item.is_dir():
          if pathlib.Path(os.path.normpath(item)+'/python.exe').exists():
            python_src_folder = os.path.normpath(item)
            break
  else:
    python_src_folder = ''

  if pathlib.Path(python_dest_folder).exists():
    print('=== Python 3 symlink found at {0}, skipping setup'.format(python_dest_folder))
  else:
    if python_src_folder != '' and pathlib.Path(python_src_folder).exists():
      print('+++ Python 3 found at {0}'.format(python_src_folder))
      d.link_dir(python_src_folder, python_dest_folder)

      if not pathlib.Path(python_dest_folder+'/python3.exe').exists():
        os.link(python_dest_folder+'/python.exe', python_dest_folder+'/python3.exe')
    else:
      error("Python 3 not found")

  if 'WindowsApps' in python_src_folder:
    print('WARNING: Detected Microsoft Store Python. Skipping pip upgrade/install due to access restrictions.')
    print('Install official Python from python.org for full functionality.')
  else:
    pip_install(python_dest_folder+'/python.exe')


def find_msvc_tools(ver, editions):
  """MSVC tools dir <ver>.* of an installed Visual Studio edition ('2022/Community', ...), or ''.
  Visual Studio 2022 installs to Program Files, its BuildTools and 2019 to Program Files (x86)."""
  for root in [os.environ.get('ProgramFiles(x86)', ''), os.environ.get('ProgramFiles', '')]:
    for edition in editions:
      versions_folder = '{0}/Microsoft Visual Studio/{1}/VC/Tools/MSVC'.format(root, edition)
      if not root or not pathlib.Path(versions_folder).exists():
        continue
      for item in pathlib.Path(versions_folder).glob(ver + ".*"):
        tools = os.path.normpath(item)
        if item.is_dir() and pathlib.Path(tools+'/bin/HostX64/x64/1033').exists() and pathlib.Path(tools+'/bin/HostX86/x86/1033').exists():
          return tools
  return ''


def setup_msvc(d, name, ver, dest, editions, install_hint):
  """dest links to MSVC <ver>; False when it is not installed."""
  dest_folder = d.path(dest)
  if pathlib.Path(dest_folder).exists():
    real_path = ""
    try:
      real_path = os.path.realpath(dest_folder)
    except OSError:
      pass

    if (not pathlib.Path(dest_folder + '/bin/HostX64/x64/1033').exists() or
       (real_path.find("Microsoft") != -1 and real_path.find(ver) == -1)):
      print(dest_folder+" contains invalid version of build tools.")
      print("...removing "+dest_folder)
      try:
        os.remove(dest_folder)
      except OSError as e:
        error("Cannot remove link {0}: {1}".format(dest_folder, e))

  if pathlib.Path(dest_folder).exists():
    print('=== {1} symlink found at {0}, skipping setup'.format(dest_folder, name))
    return True
  src_folder = find_msvc_tools(ver, editions)
  if src_folder == '':
    print('--- {0} not found, install {1} and re-run setup'.format(name, install_hint))
    return False
  print('+++ {1} found at {0}'.format(src_folder, name))
  d.link_dir(src_folder, dest_folder)
  return True


def setup_vs142(d):
  return setup_msvc(d, 'VC2019', '14.29', 'vc2019_16.11.34',
                    ['2022/BuildTools', '2022/Community', '2022/Enterprise', '2022/Professional',
                     '2019/BuildTools', '2019/Community', '2019/Enterprise', '2019/Professional'],
                    'VisualStudio 2019 16.11.34+')


def setup_vs143(d):
  return setup_msvc(d, 'VC2022', '14.44', 'vc2022_17.14.4',
                    ['2022/BuildTools', '2022/Community', '2022/Enterprise', '2022/Professional'], 'VisualStudio 2022 17.14.4+')


def setup_winsdk_100(d):
  winsdk_dest_folder = d.path('win.sdk.100')
  if pathlib.Path(winsdk_dest_folder).exists():
    print('=== Windows 10 SDK symlink found at {0}, skipping setup'.format(winsdk_dest_folder))
    return True
  winsdk_src_folder = '{0}/Windows Kits/10'.format(os.environ['ProgramFiles(x86)'])
  if not pathlib.Path(winsdk_src_folder+'/include/10.0.19041.0').exists():
    print('--- Windows 10 SDK not found, install Windows SDK and re-run setup')
    return False
  print('+++ Windows 10 SDK found at {0}'.format(winsdk_src_folder))
  d.link_dir(winsdk_src_folder, winsdk_dest_folder)
  return True


def setup_winsdk_81(d, check_again_after_download=True):
  winsdk_dest_folder = d.path('win.sdk.81')
  if pathlib.Path(winsdk_dest_folder).exists():
    print('=== Windows 8.1 SDK symlink found at {0}, skipping setup'.format(winsdk_dest_folder))
    return
  winsdk_src_folder = '{0}/Windows Kits/8.1'.format(os.environ['ProgramFiles(x86)'])
  if pathlib.Path(winsdk_src_folder+'/include').exists():
    print('+++ Windows 8.1 SDK found at {0}'.format(winsdk_src_folder))
    d.link_dir(winsdk_src_folder, winsdk_dest_folder)
    return
  print('--- Windows 8.1 SDK not found, install Windows SDK and re-run setup')
  if not check_again_after_download:
    error("Windows 8.1 SDK is required but not found at '{0}'".format(winsdk_src_folder))
  installer = d.download("https://aka.ms/vs/15/release/vs_buildtools.exe", "vs140/vs_buildtools.exe")
  run(installer + " --wait --passive --add Microsoft.VisualStudio.Component.Windows81SDK ")
  setup_winsdk_81(d, False)


def setup_microsoft_tools(d):
  """MSVC 14.29 and 14.44 and the Windows SDKs; installs the missing ones with the Visual Studio Build Tools."""
  missing = [setup for setup in [setup_vs142, setup_vs143, setup_winsdk_100] if not setup(d)]
  setup_winsdk_81(d)
  if not missing:
    return
  installer = d.download('https://aka.ms/vs/17/release/vs_buildtools.exe')
  run(installer + " --wait --passive update")
  run(installer + " --wait --passive --addProductLang en-US --add " +
    " Microsoft.VisualStudio.Component.Roslyn.Compiler" +
    " Microsoft.Component.MSBuild" +
    " Microsoft.VisualStudio.Component.CoreBuildTools" +
    " Microsoft.VisualStudio.Workload.MSBuildTools" +
    " Microsoft.VisualStudio.Component.Windows10SDK" +
    " Microsoft.VisualStudio.Component.VC.CoreBuildTools" +
    " Microsoft.VisualStudio.Component.VC.Redist.14.Latest" +
    " Microsoft.VisualStudio.Component.TestTools.BuildTools" +
    " Microsoft.Net.Component.4.7.2.TargetingPack" +
    " Microsoft.VisualStudio.Component.VC.ASAN" +
    " Microsoft.VisualStudio.Component.TextTemplating" +
    " Microsoft.VisualStudio.Component.VC.CoreIde" +
    " Microsoft.VisualStudio.ComponentGroup.NativeDesktop.Core" +
    " Microsoft.VisualStudio.Component.Windows10SDK.19041" +
    " Microsoft.VisualStudio.ComponentGroup.VC.Tools.142.x86.x64" +
    " Microsoft.Component.VC.Runtime.UCRTSDK" +
    " Microsoft.VisualStudio.Component.VC.140" +
    " Microsoft.VisualStudio.Workload.VCTools" +
    " Microsoft.VisualStudio.Component.VC.14.29.16.11.x86.x64 " +
    " Microsoft.VisualStudio.Component.VC.14.29.16.11.ARM64 " +
    " Microsoft.VisualStudio.Component.VC.14.29.16.11.ATL " +
    " Microsoft.VisualStudio.Component.VC.14.44.17.14.x86.x64 " +
    " Microsoft.VisualStudio.Component.VC.14.44.17.14.ARM64 " +
    " Microsoft.VisualStudio.Component.VC.14.44.17.14.ATL " )
  for setup in missing:
    if not setup(d):
      error("{0} is required but not found after installing the Visual Studio Build Tools".format(setup.__name__[len('setup_'):]))


def setup_llvm(d):
  llvm_dest_folder = d.path('LLVM-21.1.8')
  if pathlib.Path(llvm_dest_folder).exists():
    print('=== LLVM 21.1.8 symlink found at {0}, skipping setup'.format(llvm_dest_folder))
    return
  llvm_src_folder = '{0}/LLVM'.format(os.environ['ProgramFiles']) #(x86)
  if not pathlib.Path(llvm_src_folder+'/bin/clang.exe').exists() or not pathlib.Path(llvm_src_folder+'/lib/clang/21').exists():
    print('--- LLVM 21.1.8 not found, trying to install')
    run(d.download('https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8/LLVM-21.1.8-win64.exe') + ' /S')

  if pathlib.Path(llvm_src_folder+'/bin').exists():
    print('+++ LLVM 21.1.8 found at {0}'.format(llvm_src_folder))
    d.link_dir(llvm_src_folder, llvm_dest_folder)
  else:
    error("LLVM 21.1.8 not found")


def setup_nasm(d):
  nasm_dest_folder = d.path('nasm')
  if pathlib.Path(nasm_dest_folder).exists():
    print('=== NASM symlink found at {0}, skipping setup'.format(nasm_dest_folder))
    return
  d.unpack(d.download('https://www.nasm.us/pub/nasm/releasebuilds/2.16/win64/nasm-2.16-win64.zip'), d.dest)
  d.link_dir(d.path('nasm-2.16'), nasm_dest_folder)
  shutil.copyfile(nasm_dest_folder+'/nasm.exe', nasm_dest_folder+'/nasmw.exe')
  shutil.copyfile(nasm_dest_folder+'/ndisasm.exe', nasm_dest_folder+'/ndisasmw.exe')
  print('+++ NASM 2.16 installed at {0}'.format(nasm_dest_folder))


def setup_ducible(d):
  ducible_dest_file = d.path('ducible.exe')
  if pathlib.Path(ducible_dest_file).exists():
    print('=== Ducible tool found at {0}, skipping setup'.format(ducible_dest_file))
    return
  d.unpack(d.download('https://github.com/jasonwhite/ducible/releases/download/v1.2.2/ducible-windows-x64-Release.zip'), d.dest)
  print('+++ Ducible tool installed at {0}'.format(d.dest))


def install_3ds_Max_SDK(d, ver, url):
  maxsdk_dest_folder = d.path('max'+ver+'.sdk')
  if pathlib.Path(maxsdk_dest_folder).exists():
    print('=== 3ds Max SDK {1} symlink found at {0}, skipping setup'.format(maxsdk_dest_folder, ver))
    return
  if not ask("Do you want to install 3ds Max {0} SDK?".format(ver), unattended_answer=False):
    return
  maxsdk_src_folder = '{0}/Autodesk/3ds Max {1} SDK'.format(os.environ['ProgramFiles'], ver)
  if not pathlib.Path(maxsdk_src_folder+'/maxsdk').exists():
    print('--- 3ds Max SDK '+ver+' not found, trying to install')
    run('msiexec /i ' + os.path.normpath(d.download(url)) + ' /qb')

  if pathlib.Path(maxsdk_src_folder+'/maxsdk').exists():
    print('+++ 3ds Max SDK {1} found at {0}'.format(maxsdk_src_folder, ver))
    d.link_dir(maxsdk_src_folder+'/maxsdk', maxsdk_dest_folder)
  else:
    print('--- 3ds Max SDK {1} not found at {0}, skipped setup'.format(maxsdk_src_folder, ver))


def setup_fmod(d):
  fmod_dest_folder = d.path(FMOD)
  if pathlib.Path(fmod_dest_folder).exists():
    print('=== FMOD symlinks found at {0}, skipping setup'.format(fmod_dest_folder))
    return
  fmod_src_folder = '{0}/FMOD SoundSystem/FMOD Studio API Windows'.format(os.environ['ProgramFiles(x86)'])
  layout = [('win32', 'x86'), ('win64', 'x64'), ('win-arm64', 'arm64')]
  if pathlib.Path(fmod_src_folder).exists():
    print('+++ FMOD found at {0}'.format(fmod_src_folder))
    for api in ['core', 'studio']:
      for platform_dir, lib_dir in layout:
        pathlib.Path(fmod_dest_folder+'/'+api+'/'+platform_dir).mkdir(parents=True, exist_ok=True)
        d.link_dir(fmod_src_folder+'/api/'+api+'/inc', fmod_dest_folder+'/'+api+'/'+platform_dir+'/inc')
        d.link_dir(fmod_src_folder+'/api/'+api+'/lib/'+lib_dir, fmod_dest_folder+'/'+api+'/'+platform_dir+'/lib')
    shutil.copyfile(fmod_src_folder+'/doc/LICENSE.TXT', fmod_dest_folder+'/LICENSE.TXT')
    shutil.copyfile(fmod_src_folder+'/doc/revision.txt', fmod_dest_folder+'/revision.txt')
  else:
    print('--- FMOD not found at {0}, creating stub folders'.format(fmod_src_folder))
    print('consider downloading and installing https://www.fmod.com/download#fmodengine - Windows Download')
    for api in ['core', 'studio']:
      for platform_dir, _ in layout:
        pathlib.Path(fmod_dest_folder+'/'+api+'/'+platform_dir+'/inc').mkdir(parents=True, exist_ok=True)


# helper code do build forwarding DLL
def _run_tool(args):
  proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
  return (proc.returncode, proc.stdout.decode('mbcs', 'replace'), proc.stderr.decode('mbcs', 'replace'))

def _dumpbin(msvc_bin, *args):
  code, out, err = _run_tool([str(pathlib.Path(msvc_bin) / 'dumpbin.exe'), '/nologo'] + list(args))
  if code != 0:
    raise RuntimeError("dumpbin {0} failed ({1}):\n{2}".format(args, code, out))
  return out.splitlines()

def _dump_imports(input_dll, msvc_bin):
  """Return {module.dll: [imported symbol, ...]} for a PE image."""
  _JUNK = {
    'Import Address Table',
    'Import Name Table',
    'time date stamp',
    'Index of first forwarder reference',
  }
  _RE_MODULE = re.compile(r'^ {4}(\S+\.dll)\s*$', re.IGNORECASE)
  _RE_SYMBOL = re.compile(r'^\s+[0-9A-Fa-f]+\s+(\S.*\S)\s*$')

  imports = {}
  current = None
  for line in _dumpbin(msvc_bin, '/imports', str(input_dll)):
    if line.strip() == 'Summary':  # trailing section table, not imports
      break
    m = _RE_MODULE.match(line)
    if m:
      current = imports.setdefault(m.group(1), [])
      continue
    if current is None:
      continue
    m = _RE_SYMBOL.match(line)
    if m and m.group(1) not in _JUNK:
      current.append(m.group(1))
  return imports

def _dump_machine(input_dll, msvc_bin):
  """Return a /MACHINE: value ('ARM64', 'X64', ...) for a PE image."""
  _RE_MACHINE = re.compile(r'^\s+([0-9A-F]+) machine \((\w+)\)')
  _MACHINES = {'AA64': 'ARM64', '8664': 'X64', '14C': 'X86', '1C4': 'ARM'}

  for line in _dumpbin(msvc_bin, '/headers', str(input_dll)):
    m = _RE_MACHINE.match(line)
    if m:
      code = m.group(1).upper()
      if code not in _MACHINES:
        raise RuntimeError("unsupported machine {0} ({1})".format(code, m.group(2)))
      return _MACHINES[code]
  raise RuntimeError("no machine field in {0}".format(input_dll))


def _build_forwarder(input_dll, ref_dll, output_dll, msvc_bin, ducible):
  """Build `output_dll`: a stub forwarding to `ref_dll`.

  input_dll   PE image whose imports drive the export list.
  ref_dll     DLL holding the real implementations, e.g. "msvcp140.dll".
  output_dll  stub to create; its file name must equal the imported module
              name, since that is how the loader resolves it.
  msvc_bin    directory containing dumpbin.exe and link.exe.
  ducible     ducible.exe that makes the stub reproducible.
  """
  input_dll, output_dll = pathlib.Path(input_dll), pathlib.Path(output_dll)
  msvc_bin = pathlib.Path(msvc_bin)
  # forwarder syntax uses the module name without extension
  ref = pathlib.Path(ref_dll).stem
  if ref.lower() == output_dll.stem.lower():
    raise ValueError("{0} would forward to itself".format(output_dll.name))

  imports = _dump_imports(input_dll, msvc_bin)
  symbols = None
  for module in imports:
    if module.lower() == output_dll.name.lower():
      symbols = imports[module]
      break
  if not symbols:
    raise ValueError("{0} imports nothing from {1}; it imports from: {2}".format(
      input_dll.name, output_dll.name, ', '.join(sorted(imports))))

  def_path = output_dll.with_suffix('.def')
  def_path.parent.mkdir(parents=True, exist_ok=True)
  def_lines = ['LIBRARY ' + output_dll.stem.upper(), 'EXPORTS']
  for s in sorted(symbols):
    def_lines.append('  {0}={1}.{0}'.format(s, ref))
  def_path.write_text('\n'.join(def_lines) + '\n', encoding='ascii')

  code, out, err = _run_tool([str(msvc_bin / 'link.exe'), '/nologo', '/DLL', '/NOENTRY',
    '/MACHINE:' + _dump_machine(input_dll, msvc_bin), '/DEF:' + str(def_path), '/OUT:' + str(output_dll)])
  if code != 0:
    raise RuntimeError("link failed ({0}):\n{1}\n{2}".format(code, out, err))
  for junk in (output_dll.with_suffix('.lib'), output_dll.with_suffix('.exp'), def_path):
    if junk.exists():
      junk.unlink()

  code, out, err = _run_tool([str(ducible), str(output_dll)])
  if code != 0:
    raise RuntimeError("ducible failed ({0}):\n{1}\n{2}".format(code, out, err))
  return output_dll


def setup_openxr(d):
  openxr_dest_folder = d.path('openxr-1.1.54')
  if pathlib.Path(openxr_dest_folder).exists():
    print('=== OpenXR symlink found at {0}, skipping setup'.format(openxr_dest_folder))
    return
  d.unpack(d.download('https://github.com/KhronosGroup/OpenXR-SDK-Source/releases/download/release-1.1.54/'
                      'openxr_loader_windows-1.1.54.zip'), openxr_dest_folder+'/openxr_loader_windows')
  d.link_dir(openxr_dest_folder+'/openxr_loader_windows/include', openxr_dest_folder+'/include')
  d.link_dir(openxr_dest_folder+'/openxr_loader_windows/Win32', openxr_dest_folder+'/win32')
  d.link_dir(openxr_dest_folder+'/openxr_loader_windows/x64', openxr_dest_folder+'/win64')
  d.link_dir(openxr_dest_folder+'/openxr_loader_windows/ARM64_uwp', openxr_dest_folder+'/win-arm64')
  msvc_dir = d.path('vc2022_17.14.4/bin/Hostx64/x64')
  openxr_loader = openxr_dest_folder+'/win-arm64/bin/openxr_loader.dll'
  _build_forwarder(openxr_loader, 'msvcp140.dll', openxr_dest_folder+'/win-arm64/bin/msvcp140_app.dll', msvc_dir,
                   d.path('ducible.exe'))
  _build_forwarder(openxr_loader, 'vcruntime140.dll', openxr_dest_folder+'/win-arm64/bin/vcruntime140_app.dll', msvc_dir,
                   d.path('ducible.exe'))
  print('+++ OpenXR 1.1.54 installed at {0}'.format(openxr_dest_folder))


def setup_fsr2_sc(d):
  ffxsc_dest_folder = d.path('FidelityFX_SC')
  if pathlib.Path(ffxsc_dest_folder).exists():
    print('=== FidelityFX_SC symlink found at {0}, skipping setup'.format(ffxsc_dest_folder))
    return
  d.unpack(d.download('https://github.com/GPUOpen-Effects/FidelityFX-FSR2/archive/refs/tags/v2.2.1.zip', 'FidelityFX-FSR2.zip'),
           d.path('.packages/'))
  d.link_dir(d.path('.packages/FidelityFX-FSR2-2.2.1/tools/sc'), ffxsc_dest_folder)
  print('+++ FidelityFX_SC 2.2.1 installed at {0}'.format(ffxsc_dest_folder))


def setup_dxc(d):
  dxc_dest_folder = d.path('DXC-1.8.2505.1')
  if pathlib.Path(dxc_dest_folder).exists():
    print('=== DXC May 2025 - Patch 1 -- 1.8.2505.1 found at {0}, skipping setup'.format(dxc_dest_folder))
    return
  binaries = d.download('https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.8.2505.1/dxc_2025_07_14.zip')
  d.unpack(d.download('https://github.com/microsoft/DirectXShaderCompiler/archive/refs/tags/v1.8.2505.1.zip'), d.path('.packages/'))
  src = d.path('.packages/DirectXShaderCompiler-1.8.2505.1')
  d.unpack(binaries, src+'/_win')
  pathlib.Path(dxc_dest_folder+'/include').mkdir(parents=True, exist_ok=True)
  pathlib.Path(dxc_dest_folder+'/lib').mkdir(parents=True, exist_ok=True)
  d.link_dir(src+'/include/dxc', dxc_dest_folder+'/include/dxc')
  d.link_dir(src+'/_win/bin/x64', dxc_dest_folder+'/lib/win64')
  d.link_dir(src+'/_win/bin/arm64', dxc_dest_folder+'/lib/win-arm64')
  shutil.copyfile(src+'/LICENSE.TXT', dxc_dest_folder+'/LICENSE.TXT')
  print('+++ DXC May 2025 - Patch 1 -- 1.8.2505.1 installed at {0}'.format(dxc_dest_folder))


def setup_agility_sdk(d):
  asdk_ver = '1.619.3'
  asdk_dest_folder = d.path('Agility.SDK.'+asdk_ver)
  if pathlib.Path(asdk_dest_folder).exists():
    print('=== Agility.SDK.{1} symlink found at {0}, skipping setup'.format(asdk_dest_folder, asdk_ver))
    return
  asdk_pkg_name = d.path('.packages/D3D12-'+asdk_ver+'.pkg')
  d.unpack(d.download('https://www.nuget.org/api/v2/package/Microsoft.Direct3D.D3D12/'+asdk_ver, 'D3D12-{0}.zip'.format(asdk_ver)),
           asdk_pkg_name)
  shutil.move(asdk_pkg_name+'/build/native', asdk_dest_folder)
  for f in ['README.md', 'distributable files.txt', 'LICENSE.txt', 'LICENSE-CODE.txt', 'Microsoft.Direct3D.D3D12.nuspec']:
    shutil.move(asdk_pkg_name+'/'+f, asdk_dest_folder)
  print('+++ Agility.SDK.{1} installed at {0}'.format(asdk_dest_folder, asdk_ver))


def setup_fidelityfx_sdk(d):
  fidelityfx_sdk_ver = '2.1.1'
  fidelityfx_sdk_dest_folder = d.path('FidelityFX-SDK-'+fidelityfx_sdk_ver)
  if pathlib.Path(fidelityfx_sdk_dest_folder).exists():
    print('=== FidelityFX SDK {1} found at {0}, skipping setup'.format(fidelityfx_sdk_dest_folder, fidelityfx_sdk_ver))
    return
  d.unpack(d.download('https://github.com/GPUOpen-LibrariesAndSDKs/FidelityFX-SDK/archive/refs/tags/v'+fidelityfx_sdk_ver+'.zip',
                      'FidelityFX-SDK-'+fidelityfx_sdk_ver+'.zip'), d.dest)
  print('+++ FidelityFX SDK {1} installed at {0}'.format(fidelityfx_sdk_dest_folder, fidelityfx_sdk_ver))


def setup_nvapi(d):
  nvapi_dest_folder = d.path('nvapi-R610')
  if pathlib.Path(nvapi_dest_folder).exists():
    print('=== nvapi symlink found at {0}, skipping setup'.format(nvapi_dest_folder))
    return
  with zipfile.ZipFile(os.path.normpath(d.download('https://github.com/NVIDIA/nvapi/archive/refs/heads/main.zip', 'nvapi-R610.zip')),
                       'r') as zip_file:
    members = [
        m for m in zip_file.namelist()
        if not (m.startswith('nvapi-main/docs/') or m.startswith('nvapi-main/Sample_Code/'))
    ]
    zip_file.extractall(d.dest, members)
  os.rename(os.path.normpath(d.path('nvapi-main')), os.path.normpath(nvapi_dest_folder))
  print('+++ nvapi-R610 installed at {0}'.format(nvapi_dest_folder))


def setup_aftermath(d):
  aftermath_dest_folder = d.path('aftermath-2025.5.0.25317')
  if pathlib.Path(aftermath_dest_folder).exists():
    print('=== Nsight Aftermath SDK symlink found at {0}, skipping setup'.format(aftermath_dest_folder))
    return
  d.unpack(d.download('https://developer.nvidia.com/downloads/assets/tools/secure/nsight-aftermath-sdk/2025_5_0/windows_x64/'
                      'NVIDIA_Nsight_Aftermath_SDK_2025.5.0.25317-windows_x64.zip', 'aftermath-2025.5.0.25317.zip'),
           aftermath_dest_folder)
  print('+++ Nsight Aftermath SDK 2025.5.0.25317 installed at {0}'.format(aftermath_dest_folder))


def setup_ags(d):
  ags_sdk_dest_folder = d.path('AGS.SDK.6.3.0')
  if pathlib.Path(ags_sdk_dest_folder).exists():
    print('=== AGS SDK symlink found at {0}, skipping setup'.format(ags_sdk_dest_folder))
    return
  package = d.download('https://github.com/GPUOpen-LibrariesAndSDKs/AGS_SDK/archive/refs/tags/v6.3.0.zip', 'AGS.SDK.6.3.0.zip')
  with zipfile.ZipFile(os.path.normpath(package), 'r') as zip_file:
    prefix = 'AGS_SDK-6.3.0/ags_lib/'
    for member in zip_file.namelist():
      if member.startswith(prefix) and not member.endswith('/'):
        rel_path = os.path.relpath(member, prefix)
        if rel_path == '.':
          continue
        target_path = os.path.join(ags_sdk_dest_folder, rel_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with zip_file.open(member) as source, open(target_path, 'wb') as target:
          target.write(source.read())
  print('+++ AGS v6.3.0 installed at {0}'.format(ags_sdk_dest_folder))


def setup_streamline(d):
  streamline_ver = '2.14.1'
  streamline_dest_folder = d.path('streamline-'+streamline_ver)
  # x64 and aarch64 ship as separate archives that share the same include/ and unpack into one
  # folder, so each is tested on the bin/<arch> only it carries - a run that dies between the
  # two leaves the other arch missing, and the folder alone would look like a finished install
  for streamline_arch, streamline_zip in [('x64', 'streamline-sdk-v'+streamline_ver+'.zip'),
                                          ('arm64', 'streamline-sdk-v'+streamline_ver+'-aarch64.zip')]:
    if pathlib.Path(streamline_dest_folder+'/bin/'+streamline_arch).exists():
      print('=== Streamline SDK {1} {2} found at {0}, skipping setup'.format(streamline_dest_folder, streamline_ver, streamline_arch))
      continue
    package = d.download('https://github.com/NVIDIA-RTX/Streamline/releases/download/v'+streamline_ver+'/'+streamline_zip)
    with zipfile.ZipFile(os.path.normpath(package), 'r') as zip_file:
      members = [m for m in zip_file.namelist() if m.startswith(('include/', 'bin/', 'lib/'))]
      zip_file.extractall(streamline_dest_folder, members)
    print('+++ Streamline SDK {1} {2} installed at {0}'.format(streamline_dest_folder, streamline_ver, streamline_arch))


def setup(d):
  setup_python(d)
  setup_microsoft_tools(d)
  setup_llvm(d)
  setup_nasm(d)
  setup_ducible(d)
  setup_fmod(d)
  setup_openxr(d)
  setup_fsr2_sc(d)
  setup_dxc(d)
  setup_agility_sdk(d)
  d.install_astcenc('astcenc-4.6.1-windows-x64.zip', 'win64')
  d.install_ispc('ispc-v1.23.0-windows.zip', 'ispc-v1.23.0-windows')
  setup_fidelityfx_sdk(d)
  setup_nvapi(d)
  setup_aftermath(d)
  setup_ags(d)
  setup_streamline(d)
  max_sdk_url = 'https://autodesk-adn-transfer.s3.us-west-2.amazonaws.com/ADN+Extranet/M%26E/Max/Autodesk+3ds+Max+{0}/SDK_3dsMax{0}.msi'
  for ver in ['2026', '2025', '2024']:
    install_3ds_Max_SDK(d, ver, max_sdk_url.format(ver))
  d.install_jam('jam-windows-arm64.zip' if HOST_ARCH == 'arm64' else 'jam-windows-x86_64.zip')
  return []


def _same_dir(a, b):
  return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def finish(d):
  """Offers to point GDEVTOOL at the toolkit and add it to the user PATH; True when either changed."""
  dest = os.path.normpath(d.dest)
  env_updated = False
  gdevtool = os.environ.get('GDEVTOOL', '')
  if gdevtool == '' or not _same_dir(gdevtool, dest):
    question = ("Environment variable 'GDEVTOOL' not found. Do you want to set it?" if gdevtool == '' else
                "Environment variable 'GDEVTOOL' points to another directory ({0}). Do you want to update it?".format(gdevtool))
    if ask(question, unattended_answer=False):
      subprocess.run(["setx", "GDEVTOOL", dest], shell=True, text=True)
      os.environ["GDEVTOOL"] = dest
      env_updated = True

  if not any(_same_dir(p, dest) for p in os.environ.get('PATH', '').split(os.pathsep) if p):
    if ask("'{0}' is not found in 'PATH' variable. Do you want to add it?".format(dest), unattended_answer=False):
      print("adding {0} to 'PATH', it may take a while...".format(dest))
      add_path_command = ('[System.Environment]::SetEnvironmentVariable("PATH", ' +
                          '"{0};" + [System.Environment]::GetEnvironmentVariable("PATH", [System.EnvironmentVariableTarget]::User), '.format(dest) +
                          '[System.EnvironmentVariableTarget]::User)')
      subprocess.run(["powershell", "-Command", add_path_command], shell=True, text=True)
      env_updated = True
  return env_updated
