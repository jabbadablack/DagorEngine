"""das layer: daScript tests ([test] functions, dastest) run by the engine's das interpreter on the host.

  target{ name:t="..."; layer:t="das"
    path:t="tests"                    // repeatable: dirs or files with tests
    project:t="tests.das_project"     // optional project used to compile the tests (module paths)
    isolated:b=yes                    // run every test file in its own process (catches crashes)
  }
"""
import json
import os
from typing import Dict

from .. import process
from ..model import CaseResult, Status, TargetResult, status_from_exit_code

DAS_ROOT = 'prog/1stPartyLibs/daScript'
DAS_JAMFILE = 'prog/1stPartyLibs/daScript/utils/daScript/jamfile'


def das_exe(ctx) -> str:
  """Mirrors prog/1stPartyLibs/daScript/utils/daScript/jamfile: tools/util/das[-64]-dev[.exe]."""
  base = 'das-64' if (ctx.host, ctx.host_arch) == ('windows', 'x86_64') else 'das'
  return os.path.join(ctx.engine_root, 'tools', 'util', base + '-dev' + ('.exe' if ctx.host == 'windows' else ''))


def dastest_filters(filters):
  # dastest selects top-level tests by name prefix
  args = []
  for f in filters:
    args += ['--test-names', f.rstrip('*')]
  return args


def cases_from_report(report: Dict) -> list:
  cases = []
  for t in report.get('tests', []):
    if t.get('skipped'):
      status = Status.SKIPPED
    else:
      status = Status.PASSED if t.get('passed') else Status.FAILED
    cases.append(CaseResult(name=t.get('name', ''), status=status, duration=t.get('time', 0) / 1e6, messages=list(t.get('messages', [])),
                            location=t.get('location', '')))
  return cases


def run(ctx, target, builds, env) -> TargetResult:
  res = TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.PASSED)
  tdir = ctx.target_dir(target.id)
  exe = das_exe(ctx)
  jamfile = os.path.join(ctx.engine_root, DAS_JAMFILE)
  if not os.path.isfile(exe) or not ctx.no_build:
    build = builds.ensure(jamfile, for_host=True)
    if build.exit_code != 0 or not os.path.isfile(exe):
      res.status = Status.ERROR
      res.message = 'cannot build the das interpreter ({})'.format(build.describe_exit())
      res.log = ctx.rel(builds.log(jamfile, for_host=True))
      return res

  das_root = os.path.join(ctx.engine_root, DAS_ROOT)
  report_path = os.path.join(tdir, 'dastest.json')
  if os.path.exists(report_path):
    os.remove(report_path)
  cmd = [exe, '-dasroot', das_root, os.path.join(das_root, 'dastest', 'dastest.das'), '--']
  for p in target.params['path']:
    cmd += ['--test', os.path.normpath(os.path.join(target.dir, p))]
  if target.params.get('project'):
    cmd += ['--test-project', target.path_param('project')]
  if target.params.get('isolated'):
    cmd.append('--isolated-mode')
  timeout = target.timeout * ctx.timeout_scale
  cmd += ['--json-file', report_path, '--timeout', str(int(timeout)), '--failures-only'] + target.args + dastest_filters(ctx.filters)

  log = os.path.join(tdir, 'output.log')
  full_env = dict(os.environ)
  full_env.update(env)
  # dastest stops itself at --timeout; the runner's own limit is a backstop for hangs outside of tests
  pr = process.run(cmd, cwd=target.dir, log_path=log, timeout=timeout + 60, env=full_env)
  res.log = ctx.rel(log)
  res.duration = pr.duration
  res.exit_code = pr.exit_code

  report = None
  if os.path.isfile(report_path):
    try:
      with open(report_path, 'r', encoding='utf-8') as f:
        report = json.load(f)
    except ValueError as e:
      res.message = 'broken dastest report: {}'.format(e)
  if report:
    res.cases = cases_from_report(report)
    if report.get('errors'):  # compilation and runtime errors outside of tests
      res.cases.append(CaseResult(name='<script errors>', status=Status.FAILED,
                                  messages=['{} test file(s) failed to compile or run, see the log'.format(report['errors']),
                                            process.tail(log, 40)]))

  if pr.timed_out:
    res.status = Status.TIMEOUT
    res.message = 'killed by the runner after {:.0f} s'.format(timeout + 60)
  elif report is None:
    res.status = Status.ERROR if pr.exit_code in (0, None) else Status.FAILED
    res.message = res.message or 'dastest wrote no report ({}), see the log'.format(pr.describe_exit())
  else:
    res.status = Status.worst([status_from_exit_code(0 if report.get('success') else 1)] + [c.status for c in res.cases])
    if res.cases and all(c.status == Status.SKIPPED for c in res.cases):
      res.status = Status.SKIPPED
  return res
