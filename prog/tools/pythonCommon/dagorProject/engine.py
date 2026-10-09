"""engine.blk: how a game project finds the engine checkout it is built with.

<project>/engine.blk holds engineRoot:t="<path>", relative to the project root or absolute. The same file is read by
the engine itself (the %engine named mount, prog/engine/osApiWrappers/namedMounts.cpp), so tools and the game find the
engine from any dir inside the project.
"""
import os
import re

ENGINE_BLK = 'engine.blk'

_ENGINE_ROOT_RE = re.compile(r'^\s*engineRoot\s*:\s*t\s*=\s*"([^"]*)"', re.MULTILINE)


class ProjectError(Exception):
  pass


def is_engine_root(path: str) -> bool:
  return os.path.isfile(os.path.join(path, 'prog', '_jBuild', 'defaults.jam'))


def norm(path: str) -> str:
  return os.path.normpath(os.path.abspath(path)).replace('\\', '/')


def read_engine_ref(project_dir: str) -> str:
  """engineRoot of <project_dir>/engine.blk as written: relative to the project or absolute."""
  fn = os.path.join(project_dir, ENGINE_BLK)
  try:
    with open(fn, 'r', encoding='utf-8') as f:
      m = _ENGINE_ROOT_RE.search(f.read())
  except OSError as e:
    raise ProjectError('cannot read {}: {}'.format(fn, e.strerror))
  if not m:
    raise ProjectError('{}: expected engineRoot:t="<path to the engine checkout>"'.format(fn))
  return m.group(1)


def read_engine_root(project_dir: str) -> str:
  """Absolute engine root named by <project_dir>/engine.blk."""
  ref = read_engine_ref(project_dir)
  root = norm(os.path.join(project_dir, ref))
  if not is_engine_root(root):
    raise ProjectError('{}: engineRoot "{}" is not a Dagor Engine checkout (no {} in it); fix it with "python project.py relink <engine dir>"'
                       .format(os.path.join(project_dir, ENGINE_BLK), ref, 'prog/_jBuild/defaults.jam'))
  return root


def relative_or_absolute(path: str, start: str, absolute=False) -> str:
  """path relative to start, or absolute when asked to or when they are on different drives."""
  path = norm(path)
  if absolute:
    return path
  try:
    return os.path.relpath(path, norm(start)).replace('\\', '/')
  except ValueError:  # different drives on Windows
    return path


def write_engine_blk(project_dir: str, engine_root: str, absolute=False):
  if not is_engine_root(engine_root):
    raise ProjectError('{} is not a Dagor Engine checkout (no prog/_jBuild/defaults.jam in it)'.format(engine_root))
  ref = relative_or_absolute(engine_root, project_dir, absolute)
  with open(os.path.join(project_dir, ENGINE_BLK), 'w', encoding='utf-8', newline='\n') as f:
    f.write('// The Dagor Engine checkout this project is built with: relative to this file or absolute.\n'
            '// Change it with "python project.py relink <engine dir>".\n'
            'engineRoot:t="{}"\n'.format(ref))
