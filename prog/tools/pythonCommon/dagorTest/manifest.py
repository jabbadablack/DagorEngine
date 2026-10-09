"""test.blk manifests: one or more target{} blocks describing how to build and run a test target.

  target{
    name:t="engine.dataBlock"    // unique id
    layer:t="cpp"                // cpp | das | ecs | scenario | exec
    tag:t="engine"               // repeatable, used for -t/--exclude-tag selection
    platform:t="windows"         // repeatable; no platform means every platform
    requires:t="gpu"             // repeatable: gpu, display, network, http_server
    timeout:r=600                // whole target, seconds
    caseTimeout:r=120            // single test case, seconds (layers that support it)
    serial:b=yes                 // never run in parallel with other targets
    args:t="--foo bar"           // extra arguments for the test executable
    ...layer specific keys, see LAYER_KEYS
  }

Relative paths are relative to the directory of the test.blk.
"""
import dataclasses
import os
import shlex
from typing import Dict, List, Optional

from ..datablock import DataBlock

LAYERS = ('cpp', 'das', 'ecs', 'scenario', 'exec')
REQUIREMENTS = ('gpu', 'display', 'network', 'http_server')

COMMON_KEYS = {'name', 'layer', 'tag', 'platform', 'requires', 'timeout', 'caseTimeout', 'serial', 'args'}
LAYER_KEYS = {
  'cpp': {'jamfile', 'exe', 'dataDir', 'exeDir'},
  'das': {'path', 'project', 'isolated'},
  'ecs': {'path', 'scene', 'game'},
  'scenario': {'path', 'scene', 'game'},
  'exec': {'command', 'cwd'},
}
REPEATABLE_KEYS = {'tag', 'platform', 'requires', 'path'}
DEFAULT_TIMEOUT = 600.0


class ManifestError(Exception):
  pass


@dataclasses.dataclass
class Target:
  id: str
  layer: str
  manifest: str                     # absolute path of the test.blk
  tags: List[str]
  platforms: List[str]
  requires: List[str]
  timeout: float
  case_timeout: float
  serial: bool
  args: List[str]
  params: Dict[str, object]         # layer specific keys; repeatable ones are lists
  project: Optional['Project'] = None

  @property
  def dir(self):
    return os.path.dirname(self.manifest)

  def path_param(self, key, default=None):
    v = self.params.get(key, default)
    if v is None:
      return None
    return os.path.normpath(os.path.join(self.dir, v))


@dataclasses.dataclass
class Project:
  """A game project root (has a test.blk with a game{} block) whose targets run inside the game."""
  root: str
  codename: str
  game_dir: str                     # runtime dir with <platform>-<arch>/ executables
  jamfile: str
  das_project: str                  # game .das_project for in-game tests


def _values(blk, key):
  return [p[1][2] for p in blk.params if p[1][0] == key]


def _single(blk, key, manifest, default=None):
  v = _values(blk, key)
  if len(v) > 1:
    raise ManifestError('{}: {} is specified {} times'.format(manifest, key, len(v)))
  return v[0] if v else default


def parse_target(blk, manifest, project=None) -> Target:
  name = _single(blk, 'name', manifest)
  layer = _single(blk, 'layer', manifest)
  if not name:
    raise ManifestError('{}: target without name'.format(manifest))
  if layer not in LAYERS:
    raise ManifestError('{}: target {} has unknown layer {!r}, expected one of {}'.format(manifest, name, layer, ', '.join(LAYERS)))
  allowed = COMMON_KEYS | LAYER_KEYS[layer]
  for _, (key, _typ, _val) in blk.params:
    if key not in allowed:
      raise ManifestError('{}: target {} has unknown key {!r} for layer {}'.format(manifest, name, key, layer))
  if blk.getBlocks():
    raise ManifestError('{}: target {} must not contain blocks'.format(manifest, name))
  requires = _values(blk, 'requires')
  for r in requires:
    if r not in REQUIREMENTS:
      raise ManifestError('{}: target {} requires unknown {!r}, expected one of {}'.format(manifest, name, r, ', '.join(REQUIREMENTS)))

  params = {}
  for key in LAYER_KEYS[layer]:
    if key in REPEATABLE_KEYS:
      params[key] = _values(blk, key)
    else:
      v = _single(blk, key, manifest)
      if v is not None:
        params[key] = v

  if layer == 'cpp':
    for key in ('jamfile', 'exe'):
      if key not in params:
        raise ManifestError('{}: cpp target {} needs {}'.format(manifest, name, key))
  if layer == 'exec' and 'command' not in params:
    raise ManifestError('{}: exec target {} needs command'.format(manifest, name))
  if layer in ('das', 'ecs', 'scenario') and not params.get('path'):
    raise ManifestError('{}: {} target {} needs path'.format(manifest, layer, name))
  if layer in ('ecs', 'scenario') and project is None:
    raise ManifestError('{}: {} target {} must be in a project with a game{{}} block in its root test.blk'.format(manifest, layer, name))

  return Target(id=name, layer=layer, manifest=os.path.abspath(manifest), tags=_values(blk, 'tag'),
                platforms=_values(blk, 'platform'), requires=requires,
                timeout=float(_single(blk, 'timeout', manifest, DEFAULT_TIMEOUT)),
                case_timeout=float(_single(blk, 'caseTimeout', manifest, 0)), serial=bool(_single(blk, 'serial', manifest, False)),
                args=shlex.split(_single(blk, 'args', manifest, '') or ''), params=params, project=project)


def load_blk(path):
  try:
    return DataBlock(path)
  except Exception as e:  # datablock.py raises pyparsing errors
    raise ManifestError('{}: cannot parse: {}'.format(path, e))


def parse_project(blk, manifest) -> Optional[Project]:
  games = blk.getBlocks('game')
  if not games:
    return None
  if len(games) > 1:
    raise ManifestError('{}: more than one game{{}} block'.format(manifest))
  g = games[0]
  root = os.path.dirname(os.path.abspath(manifest))
  codename = _single(g, 'codename', manifest)
  if not codename:
    raise ManifestError('{}: game{{}} needs codename'.format(manifest))
  return Project(root=root, codename=codename, game_dir=os.path.normpath(os.path.join(root, _single(g, 'dir', manifest, 'game'))),
                 jamfile=os.path.normpath(os.path.join(root, _single(g, 'jamfile', manifest, 'prog/jamfile'))),
                 das_project=_single(g, 'dasProject', manifest, ''))


def load_targets(path, project=None) -> List[Target]:
  blk = load_blk(path)
  for b in blk.getBlocks():
    if b.name not in ('target', 'game'):
      raise ManifestError('{}: unexpected block {}{{}}, expected target{{}} or game{{}}'.format(path, b.name))
  return [parse_target(b, path, project) for b in blk.getBlocks('target')]
