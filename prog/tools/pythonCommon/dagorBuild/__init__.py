"""Building the engine and game projects: the host, the engine tools and what a project's build.py is given.

A project's prog/build.py builds its components (code, shaders, assets, vromfs, ...) in its own order:
  python build.py [component ...] [arch:<arch>] [--dry-run]
with every component of the project when none is named. dng.py build (cli.py) runs them for the engine projects.
"""
import multiprocessing
import os
import platform
import subprocess
import sys

ENGINE_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))

# components that dng.py build hands to every project; a project skips the ones it doesn't have
COMPONENTS = ('code', 'shaders', 'assets', 'vromfs', 'gui', 'tools')


def _host():
  if sys.platform.startswith('win'):
    cpu = os.environ.get('PROCESSOR_IDENTIFIER', '')
    arm = os.environ.get('PROCESSOR_ARCHITECTURE', '') == 'ARM64' or ('ARMv' in cpu and '64-bit' in cpu)
    return 'windows', 'arm64' if arm else 'x86_64'
  if sys.platform.startswith('darwin'):
    return 'macOS', 'x86_64'
  if sys.platform.startswith('linux'):
    return 'linux', platform.uname().machine
  sys.exit('unsupported platform {}'.format(sys.platform))


HOST, HOST_ARCH = _host()
TOOLS_DIR = os.path.join(ENGINE_ROOT, 'tools', 'dagor_cdk', '{}-{}'.format(HOST, HOST_ARCH))


def tool(name):
  """An engine tool built by dng.py build cdk, e.g. tool('daBuild-dev')."""
  return os.path.join(TOOLS_DIR, name + ('.exe' if HOST == 'windows' else ''))


VROMFS_PACKER = tool('vromfsPacker-dev')
DABUILD = tool('daBuild-dev')
DABUILD_CMD = [DABUILD, '-jobs:{}'.format(multiprocessing.cpu_count()), '-q']
FONTGEN = tool('fontgen2-dev')


class Build:
  """One build: what to build and how; run() records failures, exit_code reports them."""

  def __init__(self, components, arch='', dry_run=False):
    self.components = components
    self.arch = arch
    self.jam_arch = ['-sPlatformArch=' + arch] if arch else []
    self.dry_run = dry_run
    self.ok = True

  def run(self, cmd, cwd='.'):
    if self.dry_run:
      print('DRY_RUN: {} > {}'.format(cwd, cmd), flush=True)
      return True
    print('--- Running: {}  in  {}'.format(cmd, cwd), flush=True)
    if isinstance(cmd, str) and HOST == 'windows' and os.path.isfile(os.path.join(cwd, cmd.split()[0])):
      cmd = '.\\' + cmd  # cmd.exe skips the current dir when NoDefaultCurrentDirectoryInExePath is set
    try:
      subprocess.run(cmd, shell=isinstance(cmd, str), check=True, cwd=cwd)
      return True
    except (subprocess.CalledProcessError, OSError) as e:
      print('FAILED: {}'.format(e), flush=True)
      self.ok = False
      return False

  def run_per_platform(self, windows=(), macOS=(), linux=(), cwd='.'):
    """Runs the host's commands in order, stopping at the first failure."""
    return all(self.run(c, cwd) for c in {'windows': windows, 'macOS': macOS, 'linux': linux}[HOST])

  @property
  def exit_code(self):
    return 0 if self.ok else 1


def parse(argv, components):
  """The build a project's build.py is asked for; components: the ones the project has, the default when none is named."""
  arch, dry_run, named = '', False, []
  for a in argv:
    if a in ('--dry-run', '-dry-run'):
      dry_run = True
    elif a.startswith('arch:'):
      arch = a[len('arch:'):]
    elif a in components or a in COMPONENTS:
      named.append(a)
    else:
      sys.exit('unknown build argument "{}": expected {}, arch:<arch> or --dry-run'.format(a, ' '.join(components)))
  return Build([c for c in components if c in named] if named else list(components), arch, dry_run)
