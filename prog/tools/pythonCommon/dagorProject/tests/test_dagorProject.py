"""Tests of dagorProject: engine.blk, the generated engine glue and project creation from templates/dng-empty."""
import os
import re
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..')))  # prog/tools: pythonCommon is importable
from pythonCommon.dagorProject import create, engine, glue  # noqa: E402
from pythonCommon.dagorProject.engine import ProjectError  # noqa: E402

ENGINE = create.engine_root()


class EngineBlkTest(unittest.TestCase):
  def setUp(self):
    self.dir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.dir, ignore_errors=True)

  def test_written_relative_and_read_back(self):
    engine.write_engine_blk(self.dir, ENGINE)
    with open(os.path.join(self.dir, 'engine.blk'), encoding='utf-8') as f:
      text = f.read()
    ref = re.search(r'engineRoot:t="([^"]*)"', text).group(1)
    if os.path.splitdrive(self.dir)[0].lower() == os.path.splitdrive(ENGINE)[0].lower():
      self.assertFalse(os.path.isabs(ref), ref)
    self.assertEqual(engine.read_engine_root(self.dir), ENGINE)

  def test_absolute_on_request(self):
    engine.write_engine_blk(self.dir, ENGINE, absolute=True)
    self.assertEqual(engine.read_engine_root(self.dir), ENGINE)
    with open(os.path.join(self.dir, 'engine.blk'), encoding='utf-8') as f:
      self.assertIn('engineRoot:t="{}"'.format(ENGINE), f.read())

  def test_the_engine_reads_only_the_engine_root_line(self):
    # prog/engine/osApiWrappers/namedMounts.cpp takes the first quoted string after "engineRoot": comments must not name it
    engine.write_engine_blk(self.dir, ENGINE)
    with open(os.path.join(self.dir, 'engine.blk'), encoding='utf-8') as f:
      lines = [l for l in f if 'engineRoot' in l]
    self.assertEqual(len(lines), 1)
    self.assertTrue(lines[0].startswith('engineRoot:t='))

  def test_missing_and_wrong_engine_fail_clearly(self):
    with self.assertRaisesRegex(ProjectError, 'cannot read'):
      engine.read_engine_root(self.dir)
    with open(os.path.join(self.dir, 'engine.blk'), 'w') as f:
      f.write('engineRoot:t="no/such/dir"\n')
    with self.assertRaisesRegex(ProjectError, 'not a Dagor Engine checkout'):
      engine.read_engine_root(self.dir)
    with self.assertRaisesRegex(ProjectError, 'not a Dagor Engine checkout'):
      engine.write_engine_blk(self.dir, self.dir)

  def test_relative_or_absolute(self):
    self.assertEqual(engine.relative_or_absolute('C:/a/b/c', 'C:/a/d'), '../b/c') if os.name == 'nt' else None
    self.assertEqual(engine.relative_or_absolute(ENGINE, ENGINE + '/x', absolute=True), ENGINE)


class GlueTest(unittest.TestCase):
  def setUp(self):
    self.dir = tempfile.mkdtemp()

  def tearDown(self):
    shutil.rmtree(self.dir, ignore_errors=True)

  def test_libs_list_comments_and_blank_lines(self):
    fn = os.path.join(self.dir, 'libs.txt')
    with open(fn, 'w') as f:
      f.write('# a comment\n\nrender_debug  # trailing\n  bloom\n')
    self.assertEqual(glue.read_libs_list(fn), ['render_debug', 'bloom'])
    self.assertEqual(glue.read_libs_list(os.path.join(self.dir, 'missing.txt')), [])

  def test_write_if_changed(self):
    fn = os.path.join(self.dir, 'sub', 'f.cmd')
    self.assertTrue(glue.write_if_changed(fn, 'a\nb\n', newline='\r\n'))
    self.assertFalse(glue.write_if_changed(fn, 'a\nb\n', newline='\r\n'))
    with open(fn, 'rb') as f:
      self.assertEqual(f.read(), b'a\r\nb\r\n')
    self.assertTrue(glue.write_if_changed(fn, 'a\n', newline='\r\n'))

  def test_engine_jam_names_root_and_location(self):
    project = glue.Project(self.dir, 'x')
    text = glue.engine_jam(project, ENGINE)
    self.assertIn('EngineRoot = {} ;'.format(ENGINE), text)
    self.assertIn('ProjectProgDir = {}/prog ;'.format(engine.norm(self.dir)), text)
    self.assertIn('Root ?= $(EngineRoot) ;', text)

  def test_unknown_lib_fails_clearly(self):
    os.makedirs(os.path.join(self.dir, 'prog'))
    engine.write_engine_blk(self.dir, ENGINE)
    with open(os.path.join(self.dir, 'prog', 'danetgamelibs.txt'), 'w') as f:
      f.write('no_such_lib\n')
    with self.assertRaisesRegex(ProjectError, 'no_such_lib is not a lib'):
      glue.setup(glue.Project(self.dir, 'x'))


class NamesTest(unittest.TestCase):
  def test_defaults_from_name(self):
    self.assertEqual(create.default_codename('MyGame'), 'my_game')
    self.assertEqual(create.default_title('MyGame'), 'My Game')
    self.assertEqual(create.default_codename('HTTPServer2'), 'http_server2')
    self.assertEqual(create.default_codename('E2eGame'), 'e2e_game')
    self.assertEqual(create.default_title('E2eGame'), 'E2e Game')

  def test_substitution_is_one_pass(self):
    tokens = [('Dng Empty', 'DngEmpty Ultra'), ('DngEmpty', 'MyGame')]  # longest first, as create() orders them
    self.assertEqual(create.substitute('Dng Empty / DngEmpty', tokens), 'DngEmpty Ultra / MyGame')
    self.assertFalse(create.tokens_left('DngEmpty Ultra', [('DngEmpty', 'DngEmpty Ultra')]))
    self.assertTrue(create.tokens_left('a DngEmpty', [('DngEmpty', 'MyGame')]))

  def test_validation(self):
    ok = dict(name='MyGame', codename='my_game', title='My Game', company='com.example', dest='C:/x')
    create.validate(**ok)
    for key, bad in (('name', 'my_game'), ('name', 'My Game'), ('codename', 'MyGame'), ('codename', '1x'),
                     ('title', ''), ('title', 'a"b'), ('company', 'example'), ('dest', 'C:/a b'), ('dest', 'C:/ä')):
      with self.subTest(key=key, value=bad), self.assertRaises(ProjectError):
        create.validate(**dict(ok, **{key: bad}))


class TemplateFilesTest(unittest.TestCase):
  def test_gitignore_fallback(self):
    d = tempfile.mkdtemp()
    try:
      for rel in ('keep.txt', 'game/run.cmd', 'game/x/big.exe', 'prog/_engine.jam', 'a/b/c.pyc', 'template.blk'):
        os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
        open(os.path.join(d, rel), 'w').close()
      with open(os.path.join(d, '.gitignore'), 'w') as f:
        f.write('/prog/_engine.jam\n/game/*\n!/game/*.cmd\n*.pyc\n')
      files = sorted(create._gitignore_files(d))
      self.assertEqual(files, ['.gitignore', 'game/run.cmd', 'keep.txt', 'template.blk'])
    finally:
      shutil.rmtree(d, ignore_errors=True)

  def test_dng_empty_tokens(self):
    _, tokens = create.read_template_blk(os.path.join(create.templates_dir(), 'dng-empty', create.TEMPLATE_BLK))
    self.assertEqual(tokens, {'bundleId': 'com.dagor.DngEmpty', 'title': 'Dng Empty', 'name': 'DngEmpty', 'codename': 'dng_empty'})


class CreateTest(unittest.TestCase):
  """Creates a real project from templates/dng-empty (no build: CI builds and tests one, see template.yaml)."""

  @classmethod
  def setUpClass(cls):
    cls.parent = tempfile.mkdtemp()
    cls.dest = os.path.join(cls.parent, 'MyGame')
    create.create('dng-empty', 'MyGame', cls.dest, company='org.test', git_init=False, log=lambda *a: None)

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.parent, ignore_errors=True)

  def path(self, rel):
    return os.path.join(self.dest, rel)

  def read(self, rel):
    with open(self.path(rel), encoding='utf-8') as f:
      return f.read()

  def test_names_are_replaced(self):
    self.assertIn("CODENAME = 'my_game'", self.read('project.py'))
    self.assertIn('windowTitle:t="My Game"', self.read('prog/gameBase/config/settings.blk'))
    self.assertIn('BundleID   = org.test.MyGame ;', self.read('prog/jamfile'))
    self.assertTrue(os.path.isfile(self.path('prog/scripts/my_game/my_game.das')))
    self.assertTrue(os.path.isfile(self.path('prog/platform/windows/my_game.rc')))
    self.assertFalse(os.path.exists(self.path('template.blk')))

  def test_no_token_is_left(self):
    for dirpath, _, filenames in os.walk(self.dest):
      for fn in filenames:
        full = os.path.join(dirpath, fn)
        self.assertNotRegex(full, 'dng_empty|DngEmpty')
        with open(full, 'rb') as f:
          data = f.read()
        if b'\0' not in data:
          self.assertNotRegex(data.decode('utf-8'), 'dng_empty|DngEmpty|Dng Empty|com\\.dagor\\.', full)

  def test_engine_glue_is_written(self):
    self.assertEqual(engine.read_engine_root(self.dest), ENGINE)
    jam = self.read('prog/_engine.jam')
    self.assertIn('ProjectProgDir = {}/prog ;'.format(engine.norm(self.dest)), jam)
    self.assertIn('include $(Root)/prog/daNetGameLibs/frame_graph_renderer/_lib.jam ;', self.read('prog/_libs.jam'))
    self.assertIn('%engine/prog/daNetGameLibs/', self.read('prog/_libs.vromfs.blk'))

  def test_generated_and_build_files_are_not_copied(self):
    for rel in ('game/windows-x86_64', 'game/compiledShaders', 'tools', 'develop/.cache'):
      self.assertFalse(os.path.exists(self.path(rel)), rel)
    self.assertTrue(os.path.isfile(self.path('game/client.cmd')))

  def test_refuses_a_non_empty_destination(self):
    with self.assertRaisesRegex(ProjectError, 'not empty'):
      create.create('dng-empty', 'MyGame', self.dest, git_init=False, log=lambda *a: None)


if __name__ == '__main__':
  unittest.main()
