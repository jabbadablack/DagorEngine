"""Generated files that connect a project to its engine (all gitignored, rewritten by setup):

  prog/_engine.jam           EngineRoot, ProjectProgLocation and Root for the project's jamfiles
  _engine.cmd, _engine.sh    DAGOR_ENGINE_ROOT and DAGOR_CDK_DIR for the develop/ and game/ scripts
  prog/_libs*                daNetGameLibs and gameLibs listed in prog/danetgamelibs.txt and prog/gamelibs.txt
                             (jam, AOT jam, vromfs, entity templates, das init, shader list), see prog/setup_package.py

Every file is written only when its content changes, so running setup before each build costs nothing.
"""
import contextlib
import io
import os
import sys
import tempfile
from typing import Dict, List

from . import engine
from .engine import ProjectError

DANETGAMELIBS_LIST = 'prog/danetgamelibs.txt'
GAMELIBS_LIST = 'prog/gamelibs.txt'

# outputs of setup_package(), relative to the project root
LIBS_OUTPUTS = {
  'jamPath': 'prog/_libs.jam',
  'jamPathAot': 'prog/_libs_aot.jam',
  'vromfsOutputPath': 'prog/_libs.vromfs.blk',
  'templateOutputPath': 'prog/gameBase/gamedata/templates/_libs.entities.blk',
  'dasInitPath': 'prog/scripts/_libs_init.das',
  'shadersPath': 'prog/shaders/_libs_shaders.blk',
}
TOOLS_DAS_INIT = 'prog/tools/_libs_init.das'

GENERATED_HEADER = 'Generated from {source} by "python project.py setup": do not edit.'


class Project:
  """A game project: root dir (with engine.blk) and the codename of its executables and main vromfs."""

  def __init__(self, root: str, codename: str):
    self.root = engine.norm(root)
    self.codename = codename

  @property
  def prog(self) -> str:
    return self.root + '/prog'

  def path(self, rel: str) -> str:
    return self.root + '/' + rel

  def engine_root(self) -> str:
    return engine.read_engine_root(self.root)


def write_if_changed(fn: str, text: str, newline='\n') -> bool:
  try:
    with open(fn, 'r', encoding='utf-8', newline='') as f:
      if f.read() == text.replace('\n', newline):
        return False
  except OSError:
    pass
  os.makedirs(os.path.dirname(fn), exist_ok=True)
  with open(fn, 'w', encoding='utf-8', newline=newline) as f:
    f.write(text)
  return True


def engine_jam(project: Project, engine_root: str) -> str:
  location = engine.relative_or_absolute(project.prog, engine_root)
  return ('# {}\n'
          '# Project jamfiles: include it (by a path relative to the jamfile), then\n'
          '#   Location = $(ProjectProgLocation)/<dir of the jamfile inside prog> ;\n'
          'EngineRoot = {} ;\n'
          'ProjectProgLocation = {} ; # this prog dir, relative to EngineRoot or absolute (see LocationDir)\n'
          'ProjectProgDir = {} ; # this prog dir, absolute\n'
          'Root ?= $(EngineRoot) ;\n').format(GENERATED_HEADER.format(source='../engine.blk'), engine_root, location, project.prog)


def engine_cmd(project: Project, engine_root: str, absolute=False) -> str:
  ref = engine.relative_or_absolute(engine_root, project.root, absolute).replace('/', '\\')
  if not os.path.isabs(ref):
    ref = '%~dp0' + ref
  return ('@rem {}\n'
          '@set "DAGOR_ENGINE_ROOT={}"\n'
          '@call "%DAGOR_ENGINE_ROOT%\\prog\\_jBuild\\make_dagor_tools_path.cmd"\n').format(
            GENERATED_HEADER.format(source='engine.blk'), ref)


def engine_sh(project: Project, engine_root: str, absolute=False) -> str:
  ref = engine.relative_or_absolute(engine_root, project.root, absolute)
  if not os.path.isabs(ref):
    ref = '$(dirname "${BASH_SOURCE[0]:-$0}")/' + ref
  return ('# {}\n'
          '# source it: . _engine.sh\n'
          'DAGOR_ENGINE_ROOT="$(cd "{}" && pwd)"\n'
          'export DAGOR_ENGINE_ROOT\n'
          '. "$DAGOR_ENGINE_ROOT/prog/_jBuild/make_dagor_tools_path.sh"\n').format(GENERATED_HEADER.format(source='engine.blk'), ref)


def read_libs_list(fn: str) -> List[str]:
  """One lib per line (path inside daNetGameLibs or gameLibs), '#' starts a comment."""
  try:
    with open(fn, 'r', encoding='utf-8') as f:
      lines = f.readlines()
  except FileNotFoundError:
    return []
  libs = []
  for line in lines:
    line = line.split('#', 1)[0].strip()
    if line:
      libs.append(line)
  return libs


def _generate_libs(project: Project, engine_root: str) -> Dict[str, str]:
  """Runs setup_package() into a temp dir and returns {output path relative to the project: content}."""
  dng_libs = read_libs_list(project.path(DANETGAMELIBS_LIST))
  game_libs = read_libs_list(project.path(GAMELIBS_LIST))
  for libs, base, list_fn in ((dng_libs, 'prog/daNetGameLibs', DANETGAMELIBS_LIST), (game_libs, 'prog/gameLibs', GAMELIBS_LIST)):
    for lib in libs:
      if not os.path.isdir(os.path.join(engine_root, base, lib)):
        raise ProjectError('{}: {} is not a lib in {}/{}'.format(project.path(list_fn), lib, engine_root, base))

  sys.path.insert(0, os.path.join(engine_root, 'prog'))
  try:
    from setup_package import setup_package
  finally:
    sys.path.pop(0)

  outputs = {}
  with tempfile.TemporaryDirectory() as tmp:
    def tmp_path(rel):
      fn = os.path.join(tmp, rel)
      os.makedirs(os.path.dirname(fn), exist_ok=True)
      return fn

    common = dict(gamelibs=game_libs, basePath=project.prog + '/', dngLibsPath=engine_root + '/prog/daNetGameLibs',
                  gamelibsBasePath=engine_root + '/prog/gameLibs', engineRoot=engine_root, gen2=True,
                  codegenSource='danetgamelibs.txt and gamelibs.txt, then python project.py setup')
    log = io.StringIO()
    cwd = os.getcwd()
    os.chdir(project.prog)  # setup_package copies sq_stubs of libs relative to the cwd
    try:
      with contextlib.redirect_stdout(log):
        setup_package(libsListOrPath=dng_libs, vromfsName=project.codename + '.vromfs.bin',
                      **{k: tmp_path(v) for k, v in LIBS_OUTPUTS.items()}, **common)
        setup_package(libsListOrPath=dng_libs, dasInitPath=tmp_path(TOOLS_DAS_INIT), forTools=True, **common)
    except Exception:
      sys.stdout.write(log.getvalue())
      raise
    finally:
      os.chdir(cwd)
    for rel in list(LIBS_OUTPUTS.values()) + [TOOLS_DAS_INIT]:
      with open(os.path.join(tmp, rel), 'r', encoding='utf-8') as f:
        outputs[rel] = f.read()
  return outputs


def setup(project: Project, verbose=False) -> List[str]:
  """Writes every generated file; returns the ones that changed."""
  engine_root = project.engine_root()
  absolute = os.path.isabs(engine.read_engine_ref(project.root))  # the scripts follow engine.blk: they move like it does
  files = {
    'prog/_engine.jam': engine_jam(project, engine_root),
    '_engine.cmd': engine_cmd(project, engine_root, absolute),
    '_engine.sh': engine_sh(project, engine_root, absolute),
  }
  files.update(_generate_libs(project, engine_root))
  changed = []
  for rel, text in files.items():
    if write_if_changed(project.path(rel), text, newline='\r\n' if rel.endswith('.cmd') else '\n'):
      changed.append(rel)
  if verbose:
    print('engine: {}'.format(engine_root))
    for rel in sorted(files):
      print('  {} {}'.format('updated  ' if rel in changed else 'unchanged', rel))
  return changed
