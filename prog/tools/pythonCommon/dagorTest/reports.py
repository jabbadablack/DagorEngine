"""run.json (the canonical result, schema v1), junit.xml (CI systems) and summary.md (CI job summaries)."""
import dataclasses
import json
import xml.etree.ElementTree as ET

from .model import Artifact, CaseResult, RunResult, Status, TargetResult

SCHEMA_VERSION = 1


def _plain(obj):
  if isinstance(obj, Status):
    return obj.value
  if dataclasses.is_dataclass(obj):
    return {f.name: _plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
  if isinstance(obj, list):
    return [_plain(v) for v in obj]
  if isinstance(obj, dict):
    return {k: _plain(v) for k, v in obj.items()}
  return obj


def to_json_dict(run: RunResult):
  d = _plain(run)
  d['schema'] = SCHEMA_VERSION
  d['status'] = run.status.value
  d['exitCode'] = run.exit_code()
  for t, td in zip(run.targets, d['targets']):
    td['counts'] = t.counts()
  return d


def write_json(run: RunResult, path):
  with open(path, 'w', encoding='utf-8') as f:
    json.dump(to_json_dict(run), f, indent=1)


def read_json(path) -> RunResult:
  with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)
  if d.get('schema') != SCHEMA_VERSION:
    raise ValueError('{}: unsupported schema {!r}'.format(path, d.get('schema')))
  targets = []
  for td in d['targets']:
    cases = [CaseResult(name=c['name'], status=Status(c['status']), duration=c['duration'], messages=c['messages'], location=c['location'],
                        artifacts=[Artifact(**a) for a in c['artifacts']]) for c in td['cases']]
    targets.append(TargetResult(id=td['id'], layer=td['layer'], tags=td['tags'], status=Status(td['status']), duration=td['duration'],
                                exit_code=td['exit_code'], message=td['message'], log=td['log'], attempts=td['attempts'], cases=cases))
  return RunResult(run_id=d['run_id'], started=d['started'], duration=d['duration'], platform=d['platform'], arch=d['arch'],
                   config=d['config'], device=d['device'], git_rev=d['git_rev'], command_line=d['command_line'], targets=targets)


def write_junit(run: RunResult, path, max_output=64 << 10):
  suites = ET.Element('testsuites', name='dagor tests', time='{:.3f}'.format(run.duration))
  for t in run.targets:
    counts = t.counts()
    suite = ET.SubElement(suites, 'testsuite', name=t.id, time='{:.3f}'.format(t.duration),
                          tests=str(max(1, len(t.cases))), failures=str(counts['failed'] + counts['timeout']),
                          errors=str(counts['error'] + (1 if t.status == Status.ERROR and not t.cases else 0)),
                          skipped=str(counts['skipped']))
    props = ET.SubElement(suite, 'properties')
    for k, v in (('layer', t.layer), ('tags', ','.join(t.tags)), ('log', t.log), ('attempts', str(t.attempts))):
      ET.SubElement(props, 'property', name=k, value=v)
    classname = '{}.{}'.format(t.layer, t.id)
    cases = t.cases or [CaseResult(name='<target>', status=t.status, duration=t.duration, messages=[t.message] if t.message else [])]
    for c in cases:
      tc = ET.SubElement(suite, 'testcase', classname=classname, name=c.name, time='{:.3f}'.format(c.duration))
      text = '\n'.join(c.messages)
      if c.location:
        text = '{}\nat {}'.format(text, c.location)
      if c.status in (Status.FAILED, Status.TIMEOUT):
        el = ET.SubElement(tc, 'failure', type=c.status.value, message=(c.messages[0] if c.messages else c.status.value)[:500])
        el.text = text
      elif c.status == Status.ERROR:
        el = ET.SubElement(tc, 'error', message=(c.messages[0] if c.messages else 'error')[:500])
        el.text = text
      elif c.status == Status.SKIPPED:
        ET.SubElement(tc, 'skipped', message=(c.messages[0] if c.messages else '')[:500])
      attachments = [p for a in c.artifacts for p in a.files.values()]
      if attachments:  # Jenkins/GitLab attachment convention
        ET.SubElement(tc, 'system-out').text = '\n'.join('[[ATTACHMENT|{}]]'.format(p) for p in attachments)
    if t.message:
      ET.SubElement(suite, 'system-err').text = t.message[:max_output]
  ET.ElementTree(suites).write(path, encoding='utf-8', xml_declaration=True)


ICONS = {'passed': 'PASS', 'failed': 'FAIL', 'timeout': 'TIMEOUT', 'error': 'ERROR', 'skipped': 'SKIP'}


def write_summary_md(run: RunResult, path, max_failures=50):
  lines = ['## Dagor tests: {}'.format(ICONS[run.status.value]), '',
           '{} on {}-{} ({}), {:.1f} s'.format(run.device, run.platform, run.arch, run.config, run.duration), '',
           '| Target | Layer | Status | Passed | Failed | Skipped | Time |', '|---|---|---|---:|---:|---:|---:|']
  for t in run.targets:
    c = t.counts()
    lines.append('| {} | {} | {} | {} | {} | {} | {:.1f} s |'.format(t.id, t.layer, ICONS[t.status.value], c['passed'],
                                                                  c['failed'] + c['timeout'] + c['error'], c['skipped'], t.duration))
  problems = [(t, c) for t in run.targets for c in t.cases if c.status in (Status.FAILED, Status.TIMEOUT, Status.ERROR)]
  broken = [t for t in run.targets if t.status in (Status.FAILED, Status.TIMEOUT, Status.ERROR) and t.message]
  if problems or broken:
    lines += ['', '### Problems', '']
    for t in broken:
      lines.append('- **{}**: {}'.format(t.id, t.message.splitlines()[0]))
    for t, c in problems[:max_failures]:
      first = c.messages[0].splitlines()[0] if c.messages and c.messages[0] else c.status.value
      lines.append('- **{}** / {}: {}'.format(t.id, c.name, first))
    if len(problems) > max_failures:
      lines.append('- ... and {} more'.format(len(problems) - max_failures))
  with open(path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines) + '\n')
