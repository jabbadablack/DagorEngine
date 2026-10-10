"""Command line of the test runner (dng.py test in the engine root)."""
import argparse
import datetime
import multiprocessing
import os
import subprocess
import sys
import time

from . import devices, discover, jam, report_html, reports, runner
from .context import RunContext, relpath_or_abs
from .manifest import LAYERS, ManifestError
from .model import RunResult, Status

DESCRIPTION = '''Builds and runs Dagor Engine and game project tests and writes reports.

Every test target is declared in a test.blk manifest (see prog/tools/pythonCommon/dagorTest/manifest.py). Engine
manifests are found under prog/, project ones under each --project root.'''

EPILOG = '''examples:
  python dng.py test                                  build and run every engine target for the host
  python dng.py test list --layer cpp
  python dng.py test run -t engine -k "engine.*" -j 8
  python dng.py test run --gpu no --junit results.xml CI without a GPU
  python dng.py test run --project ../MyGame --no-engine
  python dng.py test report _output/test_results/latest  regenerate reports of a run

exit codes: 0 all selected targets passed or were skipped, 1 test failures or timeouts, 2 errors (build failures,
broken manifests, harness or runner errors)'''


def _csv(values):
  out = []
  for v in values or []:
    out += [x.strip() for x in v.split(',') if x.strip()]
  return out


def make_parser(host, host_arch):
  p = argparse.ArgumentParser(prog='dng.py test', description=DESCRIPTION, epilog=EPILOG,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('command', nargs='?', default='run', choices=['run', 'build', 'list', 'report'])
  p.add_argument('run_dir', nargs='?', help='for "report": the run dir (or its run.json) to regenerate reports for')
  sel = p.add_argument_group('selection')
  sel.add_argument('--project', action='append', default=[], metavar='DIR', help='game project root to include (repeatable)')
  sel.add_argument('--no-engine', action='store_true', help="don't include the engine's own targets")
  sel.add_argument('--layer', action='append', metavar='L', help='layers to run, comma separated: ' + ', '.join(LAYERS))
  sel.add_argument('-t', '--tag', action='append', metavar='TAG', help='run targets with any of these tags')
  sel.add_argument('--exclude-tag', action='append', metavar='TAG', help='skip targets with any of these tags')
  sel.add_argument('-k', action='append', metavar='GLOB', dest='patterns', help='target id glob, e.g. "gameLibs.*" (repeatable)')
  sel.add_argument('-c', '--case', action='append', metavar='NAME', dest='cases',
                   help='only test cases matching NAME (repeatable; passed to the test executables)')
  cfg = p.add_argument_group('build configuration')
  cfg.add_argument('--platform', default=host, help='jam Platform (default: %(default)s)')
  cfg.add_argument('--arch', default=host_arch, help='jam PlatformArch (default: %(default)s)')
  cfg.add_argument('--config', default='dev', help='jam Config (default: %(default)s)')
  cfg.add_argument('--jam-arg', action='append', default=[], metavar='ARG', help='extra jam argument, e.g. -sSanitize=address')
  cfg.add_argument('--no-build', action='store_true', help='use the executables that are already built')
  ex = p.add_argument_group('execution')
  ex.add_argument('--device', default='local', help='device backend[:id] (default: local); see dagorTest/devices')
  ex.add_argument('-j', '--jobs', type=int, default=max(1, min(8, multiprocessing.cpu_count() // 2)),
                  help='targets run in parallel (default: %(default)s); GPU and serial targets always run alone')
  ex.add_argument('--retries', type=int, default=0, help='rerun failed targets up to N times; passing reruns are reported as FLAKY')
  ex.add_argument('--timeout-scale', type=float, default=1.0, help='multiply every timeout, e.g. 3 for sanitizer builds')
  ex.add_argument('--gpu', choices=['auto', 'yes', 'no'], default='auto',
                  help='auto: GPU targets run and skip themselves without a device; yes: a missing device is an error; no: skip them')
  ex.add_argument('--network', action='store_true', help='run targets that need internet access')
  ex.add_argument('--update-references', action='store_true', help='replace missing or mismatching reference images')
  ex.add_argument('--fail-fast', action='store_true', help='stop starting targets after the first problem')
  out = p.add_argument_group('output')
  out.add_argument('--out', metavar='DIR', help='run dir (default: <output>/test_results/<run id>)')
  out.add_argument('--junit', metavar='FILE', help='also write JUnit XML here')
  out.add_argument('--json', metavar='FILE', help='also write run.json here')
  out.add_argument('--html', metavar='FILE', help='also write the HTML report here')
  out.add_argument('--summary-md', metavar='FILE', help='append a markdown summary here (e.g. $GITHUB_STEP_SUMMARY)')
  out.add_argument('-v', '--verbose', action='store_true')
  return p


def git_rev(root):
  try:
    return subprocess.run(['git', '-C', root, 'rev-parse', '--short', 'HEAD'], capture_output=True, text=True, timeout=10).stdout.strip()
  except (OSError, subprocess.SubprocessError):
    return ''


def write_reports(run: RunResult, run_dir, args):
  reports.write_json(run, os.path.join(run_dir, 'run.json'))
  reports.write_junit(run, os.path.join(run_dir, 'junit.xml'))
  reports.write_summary_md(run, os.path.join(run_dir, 'summary.md'))
  report_html.write_html(run, run_dir, os.path.join(run_dir, 'report.html'))
  if getattr(args, 'json', None):
    reports.write_json(run, args.json)
  if getattr(args, 'junit', None):
    reports.write_junit(run, args.junit)
  if getattr(args, 'html', None):
    # images are referenced relative to the run dir, so a copy elsewhere must inline them
    report_html.write_html(run, run_dir, args.html, image_budget=1 << 40)
  if getattr(args, 'summary_md', None):
    with open(os.path.join(run_dir, 'summary.md'), 'r', encoding='utf-8') as src, open(args.summary_md, 'a', encoding='utf-8') as dst:
      dst.write(src.read())


def print_summary(run: RunResult, run_dir):
  totals = {s: 0 for s in Status}
  for t in run.targets:
    totals[t.status] += 1
  print('\n{} targets: {}'.format(len(run.targets), ', '.join('{} {}'.format(n, s.value) for s, n in totals.items() if n)))
  for t in run.targets:
    if t.status in (Status.FAILED, Status.TIMEOUT, Status.ERROR):
      print('  {} {}{}'.format(runner.STATUS_LABELS[t.status], t.id, ': ' + t.message.splitlines()[0] if t.message else ''))
      for c in t.cases:
        if c.status in (Status.FAILED, Status.TIMEOUT, Status.ERROR):
          first = c.messages[0].splitlines()[0] if c.messages and c.messages[0] else ''
          print('       {} {}: {}'.format(runner.STATUS_LABELS[c.status], c.name, first))
  print('report: {}'.format(os.path.join(run_dir, 'report.html')))


def cmd_report(args):
  path = args.run_dir or ''
  run_json = path if path.endswith('.json') else os.path.join(path, 'run.json')
  if not os.path.isfile(run_json):
    print('error: {} not found'.format(run_json), file=sys.stderr)
    return 2
  run = reports.read_json(run_json)
  write_reports(run, os.path.dirname(os.path.abspath(run_json)), args)
  print_summary(run, os.path.dirname(os.path.abspath(run_json)))
  return run.exit_code()


def main(argv, engine_root, host, host_arch, tools_dir):
  args = make_parser(host, host_arch).parse_args(argv)
  if args.command == 'report':
    return cmd_report(args)

  try:
    targets = [] if args.no_engine else discover.discover_engine(engine_root)
    for proj in args.project:
      targets += discover.discover_project(proj)
    discover.check_unique(targets)
  except ManifestError as e:
    print('error: {}'.format(e), file=sys.stderr)
    return 2
  targets = runner.select(targets, layers=_csv(args.layer), tags=_csv(args.tag), exclude_tags=_csv(args.exclude_tag),
                          patterns=args.patterns, platform=args.platform)

  if args.command == 'list':
    for t in targets:
      req = ' requires ' + ','.join(t.requires) if t.requires else ''
      print('{:<40} {:<9} {:<24} {}{}'.format(t.id, t.layer, ','.join(t.tags), relpath_or_abs(t.manifest, engine_root), req))
    print('{} targets'.format(len(targets)))
    return 0

  started = datetime.datetime.now()
  run_id = '{}-{}-{}'.format(started.strftime('%Y%m%d-%H%M%S'), args.platform, args.arch)
  output_root = os.environ.get('GOUT_ROOT') or os.path.join(engine_root, '_output')
  run_dir = os.path.abspath(args.out or os.path.join(output_root, 'test_results', run_id))
  os.makedirs(run_dir, exist_ok=True)

  try:
    device = devices.create(args.device)
  except RuntimeError as e:
    print('error: {}'.format(e), file=sys.stderr)
    return 2
  if not device.available():
    print('error: device {} is not available'.format(device.describe()), file=sys.stderr)
    return 2

  ctx = RunContext(engine_root=engine_root, host=host, host_arch=host_arch, platform=args.platform, arch=args.arch, config=args.config,
                   run_dir=run_dir, tools_dir=tools_dir, gpu=args.gpu, network=args.network, update_references=args.update_references,
                   timeout_scale=args.timeout_scale, filters=args.cases or [], jam_args=args.jam_arg, no_build=args.no_build,
                   verbose=args.verbose, device=device)
  device.prepare(ctx)
  builds = jam.BuildCache(ctx)
  print('{} targets, run dir {}'.format(len(targets), run_dir), flush=True)
  t0 = time.monotonic()
  runner.build_all(ctx, [t for t in targets if runner.unmet_requirement(ctx, t) is None], builds)
  if args.command == 'build':
    failed = [j for j, r in builds.results.items() if r.exit_code != 0]
    for j in failed:
      print('build failed: {} (log {})'.format(j.split('|')[0], builds.logs[j]))
    return 2 if failed else 0

  results = runner.run_targets(ctx, targets, builds, jobs=args.jobs, retries=args.retries, fail_fast=args.fail_fast)
  if args.gpu == 'yes':  # an unavailable GPU is an error when GPU tests were explicitly requested
    for r, t in zip(results, targets):
      if 'gpu' in t.requires and r.status == Status.SKIPPED and r.exit_code == 77:
        r.status = Status.ERROR
        r.message = 'GPU required (--gpu yes) but unavailable: ' + r.message
  run = RunResult(run_id=run_id, started=started.isoformat(timespec='seconds'), duration=time.monotonic() - t0, platform=args.platform,
                  arch=args.arch, config=args.config, device=device.describe(), git_rev=git_rev(engine_root), command_line=list(argv),
                  targets=results)
  write_reports(run, run_dir, args)
  latest = os.path.join(os.path.dirname(run_dir), 'latest.txt')
  if os.path.dirname(run_dir) == os.path.join(output_root, 'test_results'):
    with open(latest, 'w') as f:
      f.write(run_dir + '\n')
  print_summary(run, run_dir)
  return run.exit_code()
