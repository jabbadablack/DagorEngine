"""Running test processes with timeouts that reliably kill the whole process tree."""
import dataclasses
import os
import signal
import subprocess
import sys
import time
from typing import Dict, List, Optional

IS_WINDOWS = sys.platform.startswith('win')


@dataclasses.dataclass
class ProcessResult:
  exit_code: Optional[int]          # None when killed on timeout
  timed_out: bool
  duration: float

  def describe_exit(self):
    if self.timed_out:
      return 'killed after timeout'
    code = self.exit_code
    if code is None:
      return 'no exit code'
    if code < 0:
      try:
        return 'killed by signal {}'.format(signal.Signals(-code).name)
      except ValueError:
        return 'killed by signal {}'.format(-code)
    if IS_WINDOWS and code >= 0xC0000000:
      return 'crashed with exception 0x{:08X}'.format(code)
    return 'exit code {}'.format(code)


def _popen_group_args():
  if IS_WINDOWS:
    return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
  return {'start_new_session': True}


def kill_tree(proc: subprocess.Popen):
  if proc.poll() is not None:
    return
  if IS_WINDOWS:
    subprocess.run(['taskkill', '/T', '/F', '/PID', str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  else:
    try:
      os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
      pass
  try:
    proc.wait(timeout=10)
  except subprocess.TimeoutExpired:
    proc.kill()


def start(cmd: List[str], cwd: str, env: Optional[Dict[str, str]] = None, log_file=None) -> subprocess.Popen:
  return subprocess.Popen(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL, stdout=log_file or subprocess.DEVNULL,
                          stderr=subprocess.STDOUT, **_popen_group_args())


def run(cmd: List[str], cwd: str, log_path: str, timeout: float, env: Optional[Dict[str, str]] = None,
        append=False) -> ProcessResult:
  """Runs cmd with stdout and stderr written to log_path; kills the process tree after timeout seconds."""
  os.makedirs(os.path.dirname(log_path), exist_ok=True)
  started = time.monotonic()
  with open(log_path, 'ab' if append else 'wb') as log:
    log.write('$ {}\n  in {}\n\n'.format(subprocess.list2cmdline(cmd), cwd).encode('utf-8', 'replace'))
    log.flush()
    try:
      proc = start(cmd, cwd, env, log)
    except OSError as e:
      log.write('cannot start: {}\n'.format(e).encode('utf-8', 'replace'))
      return ProcessResult(exit_code=None, timed_out=False, duration=0.0)
    try:
      code = proc.wait(timeout=timeout if timeout > 0 else None)
      return ProcessResult(exit_code=code, timed_out=False, duration=time.monotonic() - started)
    except subprocess.TimeoutExpired:
      kill_tree(proc)
      log.write('\n*** killed by the test runner after {:.0f} s timeout ***\n'.format(timeout).encode('utf-8'))
      return ProcessResult(exit_code=None, timed_out=True, duration=time.monotonic() - started)
    except BaseException:  # Ctrl+C: don't leave the test process behind
      kill_tree(proc)
      raise


def tail(path: str, max_lines=60, max_bytes=64 << 10) -> str:
  try:
    with open(path, 'rb') as f:
      f.seek(0, os.SEEK_END)
      size = f.tell()
      f.seek(max(0, size - max_bytes))
      text = f.read().decode('utf-8', 'replace')
  except OSError:
    return ''
  return '\n'.join(text.splitlines()[-max_lines:])
