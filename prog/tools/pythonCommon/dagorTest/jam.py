"""Building test targets with jam and locating the built executables."""
import os
import shlex
import shutil
import sys
import threading
from typing import Dict, List

from . import process
from .context import RunContext

BUILD_TIMEOUT = 3 * 3600


def jam_command(ctx: RunContext, jamfile: str, for_host=False) -> List[str]:
  # Root comes from the jamfile itself (relative, or from a project's _engine.jam)
  platform, arch, config = (ctx.host, ctx.host_arch, 'dev') if for_host else (ctx.platform, ctx.arch, ctx.config)
  cmd = [shutil.which('jam') or 'jam', '-q', '-sPlatform=' + platform, '-sPlatformArch=' + arch, '-sConfig=' + config]
  if os.path.basename(jamfile) != 'jamfile':
    cmd.append('-f' + os.path.basename(jamfile))
  return cmd + ctx.jam_args


def build(ctx: RunContext, jamfile: str, log_path: str, for_host=False) -> process.ProcessResult:
  return process.run(jam_command(ctx, jamfile, for_host), cwd=os.path.dirname(jamfile), log_path=log_path, timeout=BUILD_TIMEOUT)


def mangled_exe_name(ctx: RunContext, target: str) -> str:
  """Mirrors MangleTargetName and AutoCompleteTargetName in prog/_jBuild/defaults.jam for console executables."""
  name = target if ctx.config == 'rel' else '{}-{}'.format(target, ctx.config)
  if ctx.is_windows_target:
    name += '.exe'
  elif ctx.platform == 'android':
    name = '{0}/{0}.apk'.format(name)
  return name


def test_exe_path(ctx: RunContext, target, exe_dir: str = None) -> str:
  """Executable of a cpp target: prog/_jBuild/unitTest.jam puts every test executable into one OutDir."""
  out_dir = exe_dir or os.path.join(ctx.output_root, 'tests', '{}-{}'.format(ctx.platform, ctx.arch))
  return os.path.join(out_dir, mangled_exe_name(ctx, target))


class BuildCache:
  """Builds every jamfile at most once per run and remembers the outcome."""

  def __init__(self, ctx: RunContext):
    self.ctx = ctx
    self.results: Dict[str, process.ProcessResult] = {}
    self.logs: Dict[str, str] = {}
    self.lock = threading.Lock()

  @staticmethod
  def _key(jamfile, for_host):
    return os.path.normcase(os.path.abspath(jamfile)) + ('|host' if for_host else '')

  def ensure(self, jamfile: str, for_host=False) -> process.ProcessResult:
    """for_host builds a host tool (e.g. the das interpreter) instead of a target executable."""
    key = self._key(jamfile, for_host)
    with self.lock:  # jam runs are serialized: concurrent builds would race on shared libs in _output
      if key not in self.results:
        log = os.path.join(self.ctx.run_dir, '_build', '{:03d}-{}.log'.format(len(self.results), os.path.basename(os.path.dirname(jamfile))))
        self.logs[key] = log
        if self.ctx.no_build:
          self.results[key] = process.ProcessResult(exit_code=0, timed_out=False, duration=0.0)
        else:
          print('building {}{}'.format(os.path.relpath(jamfile, self.ctx.engine_root), ' (host)' if for_host else ''), flush=True)
          self.results[key] = build(self.ctx, jamfile, log, for_host)
      return self.results[key]

  def log(self, jamfile: str, for_host=False) -> str:
    return self.logs[self._key(jamfile, for_host)]

  def ensure_command(self, command: str, cwd: str) -> process.ProcessResult:
    """Runs a project's own build command (e.g. game{ build:t= }) at most once per run."""
    key = 'cmd|' + os.path.normcase(os.path.abspath(cwd)) + '|' + command
    with self.lock:
      if key not in self.results:
        log = os.path.join(self.ctx.run_dir, '_build', '{:03d}-{}.log'.format(len(self.results), os.path.basename(cwd)))
        self.logs[key] = log
        if self.ctx.no_build:
          self.results[key] = process.ProcessResult(exit_code=0, timed_out=False, duration=0.0)
        else:
          print('building {} ({})'.format(cwd, command), flush=True)
          self.results[key] = process.run(shlex.split(command.format(python=sys.executable)), cwd=cwd, log_path=log,
                                          timeout=BUILD_TIMEOUT)
      return self.results[key]

  def command_log(self, command: str, cwd: str) -> str:
    return self.logs['cmd|' + os.path.normcase(os.path.abspath(cwd)) + '|' + command]
