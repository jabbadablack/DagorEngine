"""Selecting, building and running targets."""
import concurrent.futures
import fnmatch
import os
import threading
import traceback
from typing import Callable, List, Optional

from . import jam, services
from .context import RunContext
from .layers import cpp, das, exec as exec_layer
from .manifest import Target
from .model import Status, TargetResult

LAYER_RUNNERS = {'cpp': cpp.run, 'das': das.run, 'exec': exec_layer.run}
STATUS_LABELS = {Status.PASSED: 'PASS', Status.FAILED: 'FAIL', Status.TIMEOUT: 'TIME', Status.ERROR: 'ERR ', Status.SKIPPED: 'SKIP'}


def register_layer(name: str, fn: Callable):
  LAYER_RUNNERS[name] = fn


def select(targets: List[Target], layers=None, tags=None, exclude_tags=None, patterns=None, platform=None) -> List[Target]:
  out = []
  for t in targets:
    if layers and t.layer not in layers:
      continue
    if tags and not set(tags) & set(t.tags):
      continue
    if exclude_tags and set(exclude_tags) & set(t.tags):
      continue
    if patterns and not any(fnmatch.fnmatchcase(t.id, p) for p in patterns):
      continue
    if platform and t.platforms and platform not in t.platforms:
      continue
    out.append(t)
  return out


def unmet_requirement(ctx: RunContext, target: Target) -> Optional[str]:
  """Why a target can't run in this environment, None when it can. http_server is provided by the runner."""
  for r in target.requires:
    if r == 'gpu' and ctx.gpu == 'no':
      return 'needs a GPU (--gpu no)'
    if r == 'display':
      if ctx.gpu == 'no':
        return 'needs a display (--gpu no)'
      if ctx.host == 'linux' and not (os.environ.get('DISPLAY') or os.environ.get('WAYLAND_DISPLAY')):
        return 'needs a display (no DISPLAY or WAYLAND_DISPLAY)'
    if r == 'network' and not ctx.network:
      return 'needs network access (--network)'
  if ctx.device.platforms and ctx.platform not in ctx.device.platforms:
    return 'device {} does not run {} executables'.format(ctx.device.describe(), ctx.platform)
  if target.layer not in LAYER_RUNNERS:
    return 'layer {} is not supported by this runner'.format(target.layer)
  return None


def build_all(ctx: RunContext, targets: List[Target], builds: jam.BuildCache):
  """Builds everything up front so test timings don't include builds and parallel runs never wait on jam."""
  for t in targets:
    if t.layer == 'cpp':
      builds.ensure(t.path_param('jamfile'))
    elif t.layer == 'das':
      builds.ensure(os.path.join(ctx.engine_root, das.DAS_JAMFILE), for_host=True)
    elif t.layer in ('ecs', 'scenario') and t.project:
      builds.ensure(t.project.jamfile)


def run_target(ctx: RunContext, target: Target, builds: jam.BuildCache) -> TargetResult:
  unmet = unmet_requirement(ctx, target)
  if unmet:
    return TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.SKIPPED, message=unmet)
  tdir = ctx.target_dir(target.id)
  os.makedirs(tdir, exist_ok=True)
  try:
    if 'http_server' in target.requires:
      with services.HttpServer(os.path.join(tdir, 'http_root'), os.path.join(tdir, 'http_server.log')) as http:
        return LAYER_RUNNERS[target.layer](ctx, target, builds, http.env())
    return LAYER_RUNNERS[target.layer](ctx, target, builds, {})
  except Exception:  # a runner bug must not lose the other targets' results
    return TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.ERROR,
                        message='test runner error:\n' + traceback.format_exc())


def run_with_retries(ctx, target, builds, retries) -> TargetResult:
  res = run_target(ctx, target, builds)
  attempt = 1
  first_failure = None
  while res.status in (Status.FAILED, Status.TIMEOUT) and attempt <= retries:
    first_failure = first_failure or res
    attempt += 1
    res = run_target(ctx, target, builds)
  res.attempts = attempt
  if first_failure and res.status == Status.PASSED:
    res.message = 'FLAKY: passed on attempt {} after: {}'.format(attempt, first_failure.message or first_failure.status.value)
  return res


class Progress:
  def __init__(self, total):
    self.total = total
    self.done = 0
    self.lock = threading.Lock()

  def report(self, res: TargetResult):
    with self.lock:
      self.done += 1
      extra = ' - ' + res.message.splitlines()[0] if res.message else ''
      c = res.counts()
      cases = ' [{} cases, {} failed]'.format(len(res.cases), c['failed'] + c['timeout'] + c['error']) if res.cases else ''
      print('[{:>{w}}/{}] {} {} ({:.1f} s){}{}'.format(self.done, self.total, STATUS_LABELS[res.status], res.id, res.duration, cases, extra,
                                                     w=len(str(self.total))), flush=True)


def run_targets(ctx: RunContext, targets: List[Target], builds: jam.BuildCache, jobs=1, retries=0, fail_fast=False) -> List[TargetResult]:
  results = {}
  progress = Progress(len(targets))
  stop = threading.Event()

  def one(t):
    if stop.is_set():
      res = TargetResult(id=t.id, layer=t.layer, tags=t.tags, status=Status.SKIPPED, message='not run: --fail-fast')
    else:
      res = run_with_retries(ctx, t, builds, retries)
      if fail_fast and res.status in (Status.FAILED, Status.TIMEOUT, Status.ERROR):
        stop.set()
    results[t.id] = res
    progress.report(res)

  # GPU and serial targets run alone: they compete for the device, or declare that they can't share the machine
  exclusive = [t for t in targets if t.serial or 'gpu' in t.requires]
  shared = [t for t in targets if t not in exclusive]
  if jobs > 1 and len(shared) > 1:
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
      for f in [pool.submit(one, t) for t in shared]:
        f.result()
  else:
    for t in shared:
      one(t)
  for t in exclusive:
    one(t)
  return [results[t.id] for t in targets]
