"""Unit tests of the runner that need nothing built."""
import json
import os
import shutil
import tempfile
import textwrap
import unittest
import xml.etree.ElementTree as ET

from pythonCommon.dagorTest import jam, manifest, report_html, reports, runner
from pythonCommon.dagorTest.context import RunContext
from pythonCommon.dagorTest.layers import cpp, das, events
from pythonCommon.dagorTest.model import Artifact, CaseResult, RunResult, Status, TargetResult, status_from_exit_code


def write(path, text):
  os.makedirs(os.path.dirname(path), exist_ok=True)
  with open(path, 'w', encoding='utf-8') as f:
    f.write(textwrap.dedent(text))
  return path


class TempDirTest(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.mkdtemp(prefix='dagorTest_')

  def tearDown(self):
    shutil.rmtree(self.tmp, ignore_errors=True)


class ManifestTest(TempDirTest):
  def test_parses_all_common_keys(self):
    path = write(os.path.join(self.tmp, 'test.blk'), '''
      target{
        name:t="a.b"; layer:t="cpp"; tag:t="x"; tag:t="y"; platform:t="windows"; requires:t="gpu"
        timeout:r=12; caseTimeout:r=3; serial:b=yes; args:t='--one "two words"'
        jamfile:t="jamfile"; exe:t="a-tests"
      }''')
    (t,) = manifest.load_targets(path)
    self.assertEqual((t.id, t.layer, t.tags, t.platforms, t.requires), ('a.b', 'cpp', ['x', 'y'], ['windows'], ['gpu']))
    self.assertEqual((t.timeout, t.case_timeout, t.serial), (12.0, 3.0, True))
    self.assertEqual(t.args, ['--one', 'two words'])
    self.assertEqual(t.path_param('jamfile'), os.path.join(self.tmp, 'jamfile'))

  def test_defaults(self):
    path = write(os.path.join(self.tmp, 'test.blk'), 'target{ name:t="e"; layer:t="exec"; command:t="true" }')
    (t,) = manifest.load_targets(path)
    self.assertEqual((t.timeout, t.case_timeout, t.serial, t.tags, t.args), (manifest.DEFAULT_TIMEOUT, 0.0, False, [], []))

  def check_error(self, text, fragment):
    path = write(os.path.join(self.tmp, 'test.blk'), text)
    with self.assertRaises(manifest.ManifestError) as e:
      manifest.load_targets(path)
    self.assertIn(fragment, str(e.exception))

  def test_rejects_unknown_key(self):
    self.check_error('target{ name:t="a"; layer:t="exec"; command:t="x"; tiemout:r=1 }', "unknown key 'tiemout'")

  def test_rejects_key_of_another_layer(self):
    self.check_error('target{ name:t="a"; layer:t="exec"; command:t="x"; exe:t="y" }', "unknown key 'exe'")

  def test_rejects_unknown_layer_and_requirement(self):
    self.check_error('target{ name:t="a"; layer:t="python" }', 'unknown layer')
    self.check_error('target{ name:t="a"; layer:t="exec"; command:t="x"; requires:t="vr" }', 'requires unknown')

  def test_rejects_missing_required_keys(self):
    self.check_error('target{ name:t="a"; layer:t="cpp"; jamfile:t="j" }', 'needs exe')
    self.check_error('target{ name:t="a"; layer:t="das" }', 'needs path')
    self.check_error('target{ layer:t="exec"; command:t="x" }', 'without name')

  def test_rejects_duplicate_single_key(self):
    self.check_error('target{ name:t="a"; name:t="b"; layer:t="exec"; command:t="x" }', 'specified 2 times')

  def test_ingame_layers_need_a_project(self):
    self.check_error('target{ name:t="a"; layer:t="ecs"; path:t="t" }', 'game{}')

  def test_rejects_unexpected_blocks(self):
    self.check_error('suite{ }', 'unexpected block')


class SelectionTest(unittest.TestCase):
  def make(self, id, layer='cpp', tags=(), platforms=()):
    return manifest.Target(id=id, layer=layer, manifest='/x/test.blk', tags=list(tags), platforms=list(platforms), requires=[],
                           timeout=1, case_timeout=0, serial=False, args=[], params={})

  def test_filters(self):
    ts = [self.make('engine.a', tags=['engine']), self.make('gameLibs.b', 'das', ['gameLibs']), self.make('x.c', platforms=['linux'])]
    ids = lambda sel: [t.id for t in sel]
    self.assertEqual(ids(runner.select(ts, layers=['das'])), ['gameLibs.b'])
    self.assertEqual(ids(runner.select(ts, tags=['engine', 'gameLibs'])), ['engine.a', 'gameLibs.b'])
    self.assertEqual(ids(runner.select(ts, exclude_tags=['engine'])), ['gameLibs.b', 'x.c'])
    self.assertEqual(ids(runner.select(ts, patterns=['engine.*', '*.c'])), ['engine.a', 'x.c'])
    self.assertEqual(ids(runner.select(ts, platform='windows')), ['engine.a', 'gameLibs.b'])


class NamingTest(unittest.TestCase):
  def ctx(self, platform, config):
    return RunContext(engine_root='/e', host='windows', host_arch='x86_64', platform=platform, arch='x86_64', config=config,
                      run_dir='/r', tools_dir='/t')

  def test_mangled_names_follow_defaults_jam(self):
    self.assertEqual(jam.mangled_exe_name(self.ctx('windows', 'dev'), 'foo-tests'), 'foo-tests-dev.exe')
    self.assertEqual(jam.mangled_exe_name(self.ctx('windows', 'rel'), 'foo-tests'), 'foo-tests.exe')
    self.assertEqual(jam.mangled_exe_name(self.ctx('linux', 'dbg'), 'foo-tests'), 'foo-tests-dbg')
    self.assertEqual(jam.mangled_exe_name(self.ctx('android', 'dev'), 'foo'), 'foo-dev/foo-dev.apk')

  def test_das_exe(self):
    self.assertTrue(das.das_exe(self.ctx('windows', 'dev')).endswith(os.path.join('tools', 'util', 'das-64-dev.exe')))

  def test_exit_codes(self):
    self.assertEqual([status_from_exit_code(c) for c in (0, 1, 2, 3, 77, None, -11, 0xC0000005)],
                     [Status.PASSED, Status.FAILED, Status.ERROR, Status.TIMEOUT, Status.SKIPPED, Status.ERROR, Status.FAILED, Status.FAILED])

  def test_catch2_filter_ors_and_escapes(self):
    self.assertEqual(cpp.catch2_filter([]), [])
    self.assertEqual(cpp.catch2_filter(['a b', 'c,d']), ['a b,c\\,d'])


class ResultCollectionTest(TempDirTest):
  JUNIT = '''<?xml version="1.0" encoding="UTF-8"?>
    <testsuites><testsuite name="x">
      <testcase classname="x.global" name="A/B" time="0.5" status="run"/>
      <testcase classname="x.global" name="A/B/s1" time="0.1" status="run"><failure type="CHECK">FAILED in s1</failure></testcase>
      <testcase classname="x.global" name="A/B/s2" time="0.2" status="run"/>
      <testcase classname="x.global" name="skippy" time="0" status="run"><skipped type="SKIP">because</skipped></testcase>
      <testcase classname="x.global" name="ok" time="0.25" status="run"/>
    </testsuite></testsuites>'''

  def events(self, lines):
    path = os.path.join(self.tmp, 'events.jsonl')
    with open(path, 'w') as f:
      for line in lines:
        f.write((json.dumps(line) if isinstance(line, dict) else line) + '\n')
    return events.read(path, lambda p: 'rel/' + os.path.basename(p))

  def test_sections_fold_into_cases_with_slashes_in_names(self):
    ev = self.events([{'event': 'caseStarted', 'case': 'A/B'}, {'event': 'caseEnded', 'case': 'A/B', 'passed': False},
                      {'event': 'caseStarted', 'case': 'skippy'}, {'event': 'caseEnded', 'case': 'skippy', 'passed': True},
                      {'event': 'caseStarted', 'case': 'ok'}, {'event': 'caseEnded', 'case': 'ok', 'passed': True}])
    cases = cpp.collect_cases(write(os.path.join(self.tmp, 'j.xml'), self.JUNIT), ev)
    self.assertEqual([(c.name, c.status) for c in cases], [('A/B', Status.FAILED), ('skippy', Status.SKIPPED), ('ok', Status.PASSED)])
    self.assertEqual(cases[0].messages, ['[s1] FAILED in s1'])
    self.assertEqual(cases[0].duration, 0.5)

  def test_events_add_failures_artifacts_and_the_unfinished_case(self):
    ev = self.events([{'event': 'caseStarted', 'case': 'ok'},
                      {'event': 'failure', 'case': 'ok', 'message': 'from a worker'},
                      {'event': 'image', 'case': 'ok', 'name': 'img', 'passed': False, 'actual': '/abs/img.actual.png',
                       'reference': '/abs/img.reference.png', 'diff': '/abs/img.diff.png', 'rms': 1.5, 'maxChannelDiff': 9,
                       'badPixelsPercent': 2},
                      {'event': 'caseEnded', 'case': 'ok', 'passed': False},
                      {'event': 'caseStarted', 'case': 'dying'},
                      '{"event":"caseEnd'])  # cut by a crash
    self.assertEqual(ev.unfinished_case, 'dying')
    self.assertEqual(ev.broken_lines, 1)
    cases = cpp.collect_cases(os.path.join(self.tmp, 'missing.xml'), ev)
    by_name = {c.name: c for c in cases}
    self.assertEqual(by_name['ok'].status, Status.FAILED)
    self.assertIn('from a worker', by_name['ok'].messages)
    (img,) = by_name['ok'].artifacts
    self.assertEqual(img.files, {'actual': 'rel/img.actual.png', 'reference': 'rel/img.reference.png', 'diff': 'rel/img.diff.png'})
    self.assertEqual(img.metrics['rms'], 1.5)
    self.assertEqual(by_name['dying'].status, Status.FAILED)

  def test_dastest_report(self):
    cases = das.cases_from_report({'tests': [{'name': 't1', 'passed': True, 'skipped': False, 'time': 1500, 'messages': []},
                                             {'name': 't2', 'passed': False, 'skipped': False, 'time': 0, 'messages': ['boom'],
                                              'location': 'f.das:3'},
                                             {'name': 't3', 'passed': False, 'skipped': True, 'time': 0, 'messages': []}]})
    self.assertEqual([(c.name, c.status) for c in cases], [('t1', Status.PASSED), ('t2', Status.FAILED), ('t3', Status.SKIPPED)])
    self.assertAlmostEqual(cases[0].duration, 0.0015)
    self.assertEqual(cases[1].location, 'f.das:3')


class ReportsTest(TempDirTest):
  def run_result(self):
    img = Artifact(kind='image', name='shot', files={'actual': 't/a.png'}, passed=False, metrics={'rms': 2.0}, message='differs')
    targets = [
      TargetResult(id='t.pass', layer='cpp', tags=['x'], status=Status.PASSED, duration=1.0,
                   cases=[CaseResult(name='c1', status=Status.PASSED, duration=0.5)]),
      TargetResult(id='t.fail', layer='das', tags=[], status=Status.FAILED, duration=2.0, message='broke', log='t.fail/output.log',
                   cases=[CaseResult(name='c2 <&>', status=Status.FAILED, messages=['boom'], location='f:1', artifacts=[img])]),
      TargetResult(id='t.err', layer='cpp', tags=[], status=Status.ERROR, message='build failed'),
      TargetResult(id='t.skip', layer='cpp', tags=[], status=Status.SKIPPED, message='needs a GPU'),
    ]
    return RunResult(run_id='r1', started='2026-01-01T00:00:00', duration=3.0, platform='windows', arch='x86_64', config='dev',
                     device='local', git_rev='abc', command_line=['run'], targets=targets)

  def test_exit_code_and_status(self):
    run = self.run_result()
    self.assertEqual((run.status, run.exit_code()), (Status.ERROR, 2))
    run.targets = run.targets[:2]
    self.assertEqual((run.status, run.exit_code()), (Status.FAILED, 1))
    run.targets = [run.targets[0]]
    self.assertEqual(run.exit_code(), 0)

  def test_json_round_trip(self):
    run = self.run_result()
    path = os.path.join(self.tmp, 'run.json')
    reports.write_json(run, path)
    back = reports.read_json(path)
    self.assertEqual(back, run)
    with open(path) as f:
      d = json.load(f)
    self.assertEqual((d['schema'], d['status'], d['exitCode']), (1, 'error', 2))
    self.assertEqual(d['targets'][1]['counts']['failed'], 1)

  def test_junit(self):
    path = os.path.join(self.tmp, 'junit.xml')
    reports.write_junit(self.run_result(), path)
    root = ET.parse(path).getroot()
    suites = {s.get('name'): s for s in root.iter('testsuite')}
    self.assertEqual(suites['t.fail'].get('failures'), '1')
    self.assertEqual(suites['t.err'].get('errors'), '1')
    case = suites['t.fail'].find('testcase')
    self.assertEqual(case.get('name'), 'c2 <&>')
    self.assertIn('at f:1', case.find('failure').text)
    self.assertIn('[[ATTACHMENT|t/a.png]]', case.find('system-out').text)
    self.assertIsNotNone(suites['t.skip'].find('testcase/skipped'))

  def test_summary_and_html(self):
    run = self.run_result()
    os.makedirs(os.path.join(self.tmp, 't'))
    with open(os.path.join(self.tmp, 't', 'a.png'), 'wb') as f:
      f.write(b'\x89PNG fake')
    reports.write_summary_md(run, os.path.join(self.tmp, 's.md'))
    with open(os.path.join(self.tmp, 's.md')) as f:
      md = f.read()
    self.assertIn('| t.fail | das | FAIL |', md)
    self.assertIn('**t.err**: build failed', md)
    html_path = os.path.join(self.tmp, 'report.html')
    report_html.write_html(run, self.tmp, html_path)
    with open(html_path, encoding='utf-8') as f:
      html = f.read()
    self.assertIn('data:image/png;base64,', html)  # inlined image
    self.assertNotIn('</script><', html.split('id="data"')[1].split('</script>')[0])  # data can't close the script tag
    report_html.write_html(run, self.tmp, html_path, image_budget=0)
    with open(html_path, encoding='utf-8') as f:
      self.assertNotIn('data:image/png', f.read())


if __name__ == '__main__':
  unittest.main()
