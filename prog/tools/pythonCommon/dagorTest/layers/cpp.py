"""cpp layer: Catch2 executables built with prog/_jBuild/unitTest.jam (main from <unittest/mainCatch2.inc.cpp>)."""
import os
import xml.etree.ElementTree as ET
from typing import Dict, List

from .. import jam, process
from ..model import CaseResult, Status, TargetResult, status_from_exit_code
from . import events as events_mod


def catch2_filter(filters: List[str]) -> List[str]:
  """Catch2 ANDs separate test spec arguments and ORs comma separated ones; we want any of the filters."""
  if not filters:
    return []
  return [','.join(f.replace(',', '\\,') for f in filters)]


def _clean_message(text: str) -> str:
  """Catch2 starts JUnit failure texts with a FAILED:/SKIPPED header line that says nothing the status doesn't."""
  lines = (text or '').strip().splitlines()
  if lines and lines[0].strip() in ('FAILED:', 'SKIPPED', 'FAILED'):
    lines = lines[1:]
  return '\n'.join(lines).strip()


def _junit_entries(path: str):
  """Yields (name, seconds, status, message) for each <testcase>; Catch2 writes one per section as 'case/section'."""
  root = ET.parse(path).getroot()
  for tc in root.iter('testcase'):
    name = tc.get('name', '')
    seconds = float(tc.get('time', '0') or 0)
    fail = tc.find('failure')
    if fail is None:
      fail = tc.find('error')
    skipped = tc.find('skipped')
    if fail is not None:
      yield name, seconds, Status.FAILED, _clean_message(fail.text or fail.get('message', ''))
    elif skipped is not None:
      yield name, seconds, Status.SKIPPED, _clean_message(skipped.text or skipped.get('message', ''))
    else:
      yield name, seconds, Status.PASSED, ''


def _owner_case(entry_name: str, case_names: List[str]) -> str:
  """Case a junit entry belongs to: case names may contain '/', so take the longest known prefix."""
  best = ''
  for c in case_names:
    if (entry_name == c or entry_name.startswith(c + '/')) and len(c) > len(best):
      best = c
  return best or entry_name


def collect_cases(junit_path: str, ev: events_mod.Events) -> List[CaseResult]:
  cases: Dict[str, CaseResult] = {}
  order = list(ev.started)
  if os.path.isfile(junit_path):
    try:
      entries = list(_junit_entries(junit_path))
    except ET.ParseError:
      entries = []  # a crashed process leaves the file unfinished; events tell what happened
    for name, seconds, status, message in entries:
      owner = _owner_case(name, ev.started)
      case = cases.get(owner)
      if case is None:
        case = cases[owner] = CaseResult(name=owner, status=Status.PASSED)
        if owner not in order:
          order.append(owner)
      case.duration = max(case.duration, seconds)
      if status == Status.FAILED:
        case.status = Status.FAILED
      elif status == Status.SKIPPED and case.status == Status.PASSED:
        case.status = Status.SKIPPED
      if message:
        section = name[len(owner) + 1:] if name != owner else ''
        case.messages.append('[{}] {}'.format(section, message) if section else message)

  for name in ev.started:  # started but not in the junit file: the process died in it
    if name not in cases:
      cases[name] = CaseResult(name=name, status=Status.PASSED if ev.ended.get(name) else Status.FAILED)
  for name, msgs in ev.failures.items():
    case = cases.setdefault(name, CaseResult(name=name, status=Status.FAILED))
    case.status = Status.FAILED
    case.messages += msgs
  for name, arts in ev.artifacts.items():
    if name in cases:
      cases[name].artifacts += arts
  return [cases[n] for n in order if n in cases]


def run(ctx, target, builds: jam.BuildCache, env: Dict[str, str]) -> TargetResult:
  res = TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.PASSED)
  tdir = ctx.target_dir(target.id)
  jamfile = target.path_param('jamfile')
  build = builds.ensure(jamfile)
  if build.exit_code != 0:
    res.status = Status.ERROR
    res.message = 'build failed ({}), see the build log'.format(build.describe_exit())
    res.log = ctx.rel(builds.log(jamfile))
    return res

  exe = jam.test_exe_path(ctx, target.params['exe'], target.path_param('exeDir'))
  if not os.path.isfile(exe):
    res.status = Status.ERROR
    res.message = 'built executable not found: {}'.format(exe)
    res.log = ctx.rel(builds.log(jamfile))
    return res

  device = ctx.device
  deployed = device.deploy(ctx, exe, target.path_param('dataDir', '.'), tdir)
  try:
    artifacts = os.path.join(tdir, 'artifacts')
    junit = os.path.join(tdir, 'junit.xml')
    for stale in (junit, os.path.join(artifacts, 'events.jsonl')):  # retries reuse the dir
      if os.path.exists(stale):
        os.remove(stale)
    args = ['--reporter', 'junit::out=' + device.remote_path(deployed, junit), '--reporter', 'detailed', '--data-dir',
            deployed.data_dir, '--artifact-dir', device.remote_path(deployed, artifacts)]
    if target.case_timeout > 0:
      args += ['--case-timeout', str(target.case_timeout * ctx.timeout_scale)]
    if ctx.update_references:
      args.append('--update-references')
    args += target.args + catch2_filter(ctx.filters)

    log = os.path.join(tdir, 'output.log')
    pr = device.run(deployed, args, env, target.timeout * ctx.timeout_scale, log)
    device.collect(deployed)
  finally:
    device.cleanup(deployed)

  res.log = ctx.rel(log)
  res.duration = pr.duration
  res.exit_code = pr.exit_code
  ev = events_mod.read(os.path.join(artifacts, 'events.jsonl'), ctx.rel)
  res.cases = collect_cases(junit, ev)

  if pr.timed_out:
    res.status = Status.TIMEOUT
    res.message = 'killed by the runner after {:.0f} s'.format(target.timeout * ctx.timeout_scale)
    _mark_unfinished(res, ev, Status.TIMEOUT, 'running when the target timed out')
  elif ev.timed_out_case is not None:
    res.status = Status.TIMEOUT
    res.message = 'test case exceeded {:.0f} s'.format(target.case_timeout * ctx.timeout_scale)
    _mark_unfinished(res, ev, Status.TIMEOUT, 'exceeded the case timeout')
  else:
    res.status = status_from_exit_code(pr.exit_code)
    if pr.exit_code not in (0, 1, 2, 3, 77):
      res.message = 'test executable {}'.format(pr.describe_exit())
      # Catch2's fatal signal handler may still close the crashing case, so fall back to the last started one
      _mark_unfinished(res, ev, Status.FAILED, 'crashed here: {}\n{}'.format(pr.describe_exit(), process.tail(log, 30)),
                       fallback_last=True)
    elif res.status == Status.ERROR:
      res.message = '; '.join(ev.infra_errors) or 'test environment error ({}), see the log'.format(pr.describe_exit())
    elif res.status == Status.SKIPPED and ev.infra_errors:
      res.message = '; '.join(ev.infra_errors)
  # a run that "passed" with failing cases (or failed without any) is reported by the worse of both
  if res.cases and res.status in (Status.PASSED, Status.SKIPPED):
    worst = Status.worst(c.status for c in res.cases)
    if worst in (Status.FAILED, Status.TIMEOUT, Status.ERROR):
      res.status = worst
  if res.status == Status.FAILED and not res.cases and not res.message:
    res.message = 'test executable {}, see the log'.format(pr.describe_exit())
  return res


def _mark_unfinished(res: TargetResult, ev, status: Status, message: str, fallback_last=False):
  name = ev.unfinished_case if ev.timed_out_case is None else ev.timed_out_case
  if not name and fallback_last and ev.started:
    name = ev.started[-1]
  if not name:
    return
  for case in res.cases:
    if case.name == name:
      case.status = status
      case.messages.append(message)
      return
  res.cases.append(CaseResult(name=name, status=status, messages=[message]))
