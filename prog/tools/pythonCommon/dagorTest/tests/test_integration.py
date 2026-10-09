"""Runs real targets through the runner: the harness failure cases of prog/engine/tests/unitTest, dastest and exec.

Needs the engine (run.py passes it); builds the unitTest executable and the das interpreter if they are missing.
"""
import os
import shutil
import sys
import tempfile
import textwrap
import unittest

from pythonCommon.dagorTest import jam, runner
from pythonCommon.dagorTest.context import RunContext
from pythonCommon.dagorTest.devices.local import LocalDevice
from pythonCommon.dagorTest.manifest import load_targets
from pythonCommon.dagorTest.model import Status
from pythonCommon.datablock import escapeBlkString

ENGINE = os.environ.get('DAGORTEST_ENGINE')
UNIT_TEST_DIR = os.path.join(ENGINE or '', 'prog', 'engine', 'tests', 'unitTest')


def blk_path(path):
  """A path as a BLK string value: ~ escapes in BLK, and Windows short names have one (C:/Users/RUNNER~1)"""
  return escapeBlkString(path.replace('\\', '/'))


def make_ctx(run_dir):
  return RunContext(engine_root=ENGINE, host=os.environ['DAGORTEST_HOST'], host_arch=os.environ['DAGORTEST_HOST_ARCH'],
                    platform=os.environ['DAGORTEST_PLATFORM'], arch=os.environ['DAGORTEST_ARCH'], config=os.environ['DAGORTEST_CONFIG'],
                    run_dir=run_dir, tools_dir='', device=LocalDevice())


@unittest.skipUnless(ENGINE, 'needs DAGORTEST_ENGINE (run through run.py)')
class IntegrationTest(unittest.TestCase):
  @classmethod
  def setUpClass(cls):
    cls.tmp = tempfile.mkdtemp(prefix='dagorTest_int_')
    cls.ctx = make_ctx(os.path.join(cls.tmp, 'run'))
    cls.builds = jam.BuildCache(cls.ctx)
    build = cls.builds.ensure(os.path.join(UNIT_TEST_DIR, 'jamfile'))
    if build.exit_code != 0:
      raise RuntimeError('cannot build the unitTest executable, see ' + cls.builds.log(os.path.join(UNIT_TEST_DIR, 'jamfile')))

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.tmp, ignore_errors=True)

  def manifest(self, name, body):
    path = os.path.join(self.tmp, name, 'test.blk')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
      f.write(textwrap.dedent(body))
    return load_targets(path)

  def harness(self, name, case, extra=''):
    (t,) = self.manifest(name, '''
      target{{ name:t="{}"; layer:t="cpp"; jamfile:t="{}"; exe:t="unitTest-tests"; dataDir:t="{}"; args:t='"{}"' {} }}
      '''.format(name, blk_path(os.path.join(UNIT_TEST_DIR, 'jamfile')), blk_path(UNIT_TEST_DIR), case, extra))
    return runner.run_target(self.ctx, t, self.builds)

  def describe(self, results):
    """What went wrong, for assertion messages: CI output is all there is to go on"""
    out = []
    for tid, r in results.items():
      out.append('{}: {} {}'.format(tid, r.status.value, r.message or ''))
      if r.log and r.status != Status.PASSED:
        try:
          with open(os.path.join(self.ctx.run_dir, r.log), 'r', encoding='utf-8', errors='replace') as f:
            out += ['    ' + l.rstrip() for l in f.readlines()[-15:]]
        except OSError:
          pass
    return '\n'.join(out)

  def only_case(self, res):
    self.assertEqual(len(res.cases), 1, res.cases)
    return res.cases[0]

  def test_passing_cases(self):
    res = self.harness('pass', '[imageCompare]')
    self.assertEqual(res.status, Status.PASSED, res.message)
    self.assertGreaterEqual(len(res.cases), 5)
    self.assertTrue(all(c.status == Status.PASSED for c in res.cases))
    self.assertTrue(os.path.isfile(os.path.join(self.ctx.run_dir, res.log)))

  def test_unexpected_logerr(self):
    res = self.harness('logerr', 'harness: unexpected logerr fails the case')
    self.assertEqual(res.status, Status.FAILED)
    case = self.only_case(res)
    self.assertEqual(case.status, Status.FAILED)
    self.assertIn('unexpected harness error', '\n'.join(case.messages))

  def test_worker_thread_logerr(self):
    res = self.harness('worker', 'harness: logerr on another thread fails the case')
    self.assertEqual(res.status, Status.FAILED)
    self.assertIn('worker thread', '\n'.join(self.only_case(res).messages))

  def test_dagor_assertion(self):
    res = self.harness('assert', 'harness: dagor assertion fails the case')
    self.assertEqual(self.only_case(res).status, Status.FAILED)

  def test_skip(self):
    res = self.harness('skip', 'harness: skipped case')
    self.assertEqual(res.status, Status.SKIPPED)
    self.assertEqual(self.only_case(res).status, Status.SKIPPED)

  def test_case_watchdog(self):
    res = self.harness('watchdog', 'harness: hung case hits the watchdog', 'caseTimeout:r=1')
    self.assertEqual(res.status, Status.TIMEOUT)
    self.assertEqual(self.only_case(res).status, Status.TIMEOUT)
    self.assertLess(res.duration, 30)

  def test_target_timeout_kills_the_process(self):
    res = self.harness('kill', 'harness: hung case hits the watchdog', 'timeout:r=3')
    self.assertEqual(res.status, Status.TIMEOUT)
    self.assertIn('killed by the runner', res.message)
    self.assertEqual(self.only_case(res).status, Status.TIMEOUT)

  def test_crash(self):
    res = self.harness('crash', 'harness: crash fails the case')
    self.assertEqual(res.status, Status.FAILED)
    case = self.only_case(res)
    self.assertEqual(case.status, Status.FAILED)
    self.assertIn('crashed here', '\n'.join(case.messages))

  def test_image_mismatch_artifacts(self):
    res = self.harness('image', 'harness: image mismatch writes artifacts')
    self.assertEqual(res.status, Status.FAILED)
    (art,) = self.only_case(res).artifacts
    self.assertEqual(art.kind, 'image')
    self.assertFalse(art.passed)
    self.assertEqual(set(art.files), {'actual', 'reference', 'diff'})
    for rel in art.files.values():
      self.assertTrue(os.path.isfile(os.path.join(self.ctx.run_dir, rel)), rel)

  def test_missing_executable(self):
    (t,) = self.manifest('missing', '''
      target{{ name:t="missing"; layer:t="cpp"; jamfile:t="{}"; exe:t="no-such-tests" }}
      '''.format(blk_path(os.path.join(UNIT_TEST_DIR, 'jamfile'))))
    res = runner.run_target(self.ctx, t, self.builds)
    self.assertEqual(res.status, Status.ERROR)
    self.assertIn('not found', res.message)

  def test_exec_exit_codes_and_http_server(self):
    script = os.path.join(self.tmp, 'http_check.py')
    with open(script, 'w') as f:
      f.write(textwrap.dedent('''
        import os, sys, urllib.request
        with open(os.path.join(os.environ['DAGOR_TEST_HTTP_ROOT'], 'x.txt'), 'w') as f:
          f.write('served')
        body = urllib.request.urlopen(os.environ['DAGOR_TEST_HTTP_URL'] + 'x.txt', timeout=10).read()
        sys.exit(0 if body == b'served' else 1)
        '''))
    py = blk_path(sys.executable)
    targets = self.manifest('exec', '''
      target{{ name:t="e.pass"; layer:t="exec"; command:t='{0} -c "import sys; sys.exit(0)"' }}
      target{{ name:t="e.fail"; layer:t="exec"; command:t='{0} -c "import sys; sys.exit(1)"' }}
      target{{ name:t="e.skip"; layer:t="exec"; command:t='{0} -c "import sys; sys.exit(77)"' }}
      target{{ name:t="e.http"; layer:t="exec"; requires:t="http_server"; command:t="{0} {1}" }}
      target{{ name:t="e.gpu"; layer:t="exec"; requires:t="gpu"; command:t='{0} -c "pass"' }}
      '''.format(py, blk_path(script)))
    by_id = {t.id: t for t in targets}
    results = {i: runner.run_target(self.ctx, by_id[i], self.builds) for i in ('e.pass', 'e.fail', 'e.skip', 'e.http')}
    self.assertEqual({i: r.status for i, r in results.items()},
                     {'e.pass': Status.PASSED, 'e.fail': Status.FAILED, 'e.skip': Status.SKIPPED, 'e.http': Status.PASSED},
                     self.describe(results))
    self.ctx.gpu = 'no'
    try:
      gpu = runner.run_target(self.ctx, by_id['e.gpu'], self.builds)
    finally:
      self.ctx.gpu = 'auto'
    self.assertEqual(gpu.status, Status.SKIPPED)
    self.assertIn('GPU', gpu.message)

  def test_dastest(self):
    tests = os.path.join(self.tmp, 'das', 'tests')
    os.makedirs(tests)
    with open(os.path.join(tests, 'sample.das'), 'w') as f:
      f.write(textwrap.dedent('''
        options gen2
        require dastest/testing_boost public

        [test]
        def test_passes(t : T?) {
            t |> equal(2, 1 + 1)
        }

        [test]
        def test_fails(t : T?) {
            t |> equal(3, 1 + 1)
        }
        '''))
    (t,) = self.manifest('das', 'target{ name:t="d"; layer:t="das"; path:t="tests" }')
    res = runner.run_target(self.ctx, t, self.builds)
    self.assertEqual(res.status, Status.FAILED, res.message)
    by_name = {c.name.split('.')[-1].split(':')[-1]: c.status for c in res.cases}
    self.assertIn(Status.PASSED, by_name.values())
    self.assertIn(Status.FAILED, by_name.values())


OUTER_SPACE_GAME = os.path.join(ENGINE or '', 'outerSpace', 'game')
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')


@unittest.skipUnless(ENGINE, 'needs DAGORTEST_ENGINE (run through run.py)')
class InGameTest(unittest.TestCase):
  """The ecs layer against the outerSpace sample's dedicated server: skipped until it is built (outerSpace/prog/build.py)."""

  @classmethod
  def setUpClass(cls):
    cls.ctx = make_ctx(tempfile.mkdtemp(prefix='dagorTest_ingame_'))
    from pythonCommon.dagorTest.layers import ingame
    from pythonCommon.dagorTest.manifest import Project
    cls.project = Project(root=cls.ctx.run_dir, codename='outer_space', game_dir=OUTER_SPACE_GAME)
    if not os.path.isfile(ingame.game_exe(cls.ctx, cls.project, 'dedicated')):
      raise unittest.SkipTest('outerSpace dedicated server is not built')
    cls.builds = jam.BuildCache(cls.ctx)

  @classmethod
  def tearDownClass(cls):
    shutil.rmtree(cls.ctx.run_dir, ignore_errors=True)

  def run_fixture(self, name, extra=''):
    path = os.path.join(self.ctx.run_dir, name, 'test.blk')
    os.makedirs(os.path.dirname(path))
    with open(path, 'w') as f:
      f.write('target{{ name:t="{}"; layer:t="ecs"; path:t="{}"; scene:t="gamedata/scenes/empty.blk" {} }}'.format(
        name, os.path.join(DATA_DIR, 'ecs', name).replace('\\', '/'), extra))
    (t,) = load_targets(path, self.project)
    return runner.run_target(self.ctx, t, self.builds)

  def test_failures_are_reported_per_test(self):
    res = self.run_fixture('failures')
    self.assertEqual(res.status, Status.FAILED, res.message)
    statuses = {c.name: c.status for c in res.cases}
    self.assertEqual(statuses, {
      'fails_an_assertion': Status.FAILED, 'panics': Status.FAILED, 'logs_an_unexpected_error': Status.FAILED,
      'fatal_stops_the_test': Status.FAILED, 'is_skipped': Status.SKIPPED, 'sub_test_fails': Status.PASSED,
      'sub_test_fails/bad': Status.FAILED, 'passes_after_failures': Status.PASSED})
    messages = {c.name: '\n'.join(c.messages) for c in res.cases}
    self.assertIn('one is not two', messages['fails_an_assertion'])
    self.assertIn('deliberate panic', messages['panics'])
    self.assertIn('unexpected in-game error', messages['logs_an_unexpected_error'])
    self.assertNotIn('never reached', messages['fatal_stops_the_test'])

  def test_hung_test_hits_its_time_limit(self):
    res = self.run_fixture('hang', 'caseTimeout:r=3')
    self.assertEqual(res.status, Status.TIMEOUT)
    self.assertEqual([(c.name, c.status) for c in res.cases], [('hangs', Status.TIMEOUT)])


if __name__ == '__main__':
  unittest.main()
