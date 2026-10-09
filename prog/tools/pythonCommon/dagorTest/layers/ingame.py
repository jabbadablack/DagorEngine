"""ecs and scenario layers: [ecs_test] functions run inside the real game in its test mode (prog/daNetGame/main/testMode.h).

  target{ name:t="..."; layer:t="ecs"      // or "scenario": functional tests that render, see test_harness/scenario.das
    path:t="tests/ecs"                // repeatable: test files or directories, relative to the test.blk
    scene:t="gamedata/scenes/test.blk" // optional: the scene the game loads (default: the game's settings)
    game:t="dedicated"                // dedicated (default for ecs, headless) or client (default for scenario)
  }

Scenario targets render at a fixed 1280x720 window (override with args:t="-config:video/resolution:t=..."), write PNG
screenshots to their output dir and compare them with references/ next to the test files.

The game comes from the project's root test.blk: game{ codename:t="my_game"; dir:t="game"; build:t="python prog/build.py code" }.
"""
import json
import os

from .. import jam, process
from ..model import CaseResult, Status, TargetResult, status_from_exit_code
from . import das as das_layer
from . import events as events_mod

SCENARIO_ARGS = ['-config:video/mode:t=windowed', '-config:video/resolution:t=1280x720', '-config:screenshots/format:t=png',
                 # no physical keyboard, mouse or joystick (values <= 0 are added to All=7): what a person does on the machine
                 # must not leak into the test; scripted input (send_action, set_axis) works without them
                 '-config:input/hidDriversInit:i=-7']
GAME_ARGS = ['-stdout', '-quiet', '-nolisten', '-nostatsd', '-nonetenc', '-nopeerauth',
             '-config:debug/useAddonVromSrc:b=yes',     # tests and test libs are read from the sources, no repacking needed
             '-config:debug/daScriptHotReload:b=no']    # running tests hold pointers into loaded scripts


def cases_from_events(ev, unfinished_message) -> list:
  cases = []
  for name in ev.started:
    if name in ev.ended:
      if ev.ended[name] and name.startswith('<'):  # passed <game startup> and <load ...> steps, omitted as in the report
        continue
      cases.append(CaseResult(name=name, status=Status.PASSED if ev.ended[name] else Status.FAILED))
    else:
      cases.append(CaseResult(name=name, status=Status.FAILED, messages=[unfinished_message]))
  return cases


def _mark(res, name, status, message):
  for case in res.cases:
    if case.name == name:
      case.status = status
      case.messages = [message]
      return


def game_exe(ctx, project, game) -> str:
  base = project.codename + ('-ded' if game == 'dedicated' else '')
  return os.path.join(project.game_dir, '{}-{}'.format(ctx.platform, ctx.arch), jam.mangled_exe_name(ctx, base))


def run(ctx, target, builds, env) -> TargetResult:
  res = TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.PASSED)
  project = target.project
  scenario = target.layer == 'scenario'
  game = target.params.get('game', 'client' if scenario else 'dedicated')
  if game not in ('dedicated', 'client'):
    res.status = Status.ERROR
    res.message = "game:t= must be dedicated or client, not {!r}".format(game)
    return res
  if project.build:
    build = builds.ensure_command(project.build, project.root)
    if build.exit_code != 0:
      res.status = Status.ERROR
      res.message = 'game build failed ({}), see the build log'.format(build.describe_exit())
      res.log = ctx.rel(builds.command_log(project.build, project.root))
      return res
  exe = game_exe(ctx, project, game)
  if not os.path.isfile(exe):
    res.status = Status.ERROR
    res.message = 'game executable not found: {} (build the {} game first)'.format(exe, game)
    return res

  tdir = ctx.target_dir(target.id)
  report_path = os.path.join(tdir, 'dastest.json')
  for stale in (report_path, os.path.join(tdir, 'events.jsonl')):
    if os.path.exists(stale):
      os.remove(stale)
  args = list(GAME_ARGS)
  for p in target.params['path']:
    args.append('-das_test:' + das_layer.das_path(os.path.join(target.dir, p)))
  args += ['-test_out:' + tdir.replace('\\', '/')]
  if target.case_timeout > 0:
    args.append('-test_timeout:{:g}'.format(target.case_timeout * ctx.timeout_scale))
  if target.params.get('scene'):
    args.append('-scene:' + target.params['scene'])
  if scenario:
    args += SCENARIO_ARGS + ['-config:screenshots/dir:t=' + os.path.join(tdir, 'screenshots').replace('\\', '/')]
  if ctx.update_references:
    args.append('-test_update_references')
  args += ['-test_filter:' + f.rstrip('*') for f in ctx.filters]
  args += target.args

  log = os.path.join(tdir, 'output.log')
  full_env = dict(os.environ)
  full_env.update(env)
  timeout = target.timeout * ctx.timeout_scale
  pr = process.run([exe] + args, cwd=project.game_dir, log_path=log, timeout=timeout, env=full_env)
  res.log = ctx.rel(log)
  res.duration = pr.duration
  res.exit_code = pr.exit_code

  ev = events_mod.read(os.path.join(tdir, 'events.jsonl'), ctx.rel)
  if os.path.isfile(report_path):
    try:
      with open(report_path, 'r', encoding='utf-8') as f:
        res.cases = das_layer.cases_from_report(json.load(f))
    except ValueError as e:
      res.message = 'broken test report: {}'.format(e)
  else:  # the game died or was stopped before writing the report: the events still tell which tests ran
    res.cases = cases_from_events(ev, 'the game exited ({})'.format(pr.describe_exit()))

  for case in res.cases:
    case.artifacts += ev.artifacts.get(case.name, [])

  if pr.timed_out:
    res.status = Status.TIMEOUT
    res.message = 'killed by the runner after {:.0f} s'.format(timeout)
    _mark(res, ev.unfinished_case, Status.TIMEOUT, 'running when the runner stopped the game')
  elif ev.timed_out_case is not None:
    res.status = Status.TIMEOUT
    res.message = 'test {} exceeded its time limit'.format(ev.timed_out_case)
    _mark(res, ev.timed_out_case, Status.TIMEOUT, 'exceeded the per test time limit')
  elif not os.path.isfile(report_path):
    res.status = Status.ERROR if pr.exit_code in (0, 2, 77, None) else Status.FAILED
    unfinished = ev.unfinished_case
    res.message = 'the game wrote no test report ({}{}), see the log'.format(
      pr.describe_exit(), ', while running ' + unfinished if unfinished else '')
  else:
    res.status = status_from_exit_code(pr.exit_code)
    if res.cases and res.status == Status.PASSED and any(c.status == Status.FAILED for c in res.cases):
      res.status = Status.FAILED
    if pr.exit_code not in (0, 1, 2, 3, 77):
      res.message = 'game {}'.format(pr.describe_exit())
  return res
