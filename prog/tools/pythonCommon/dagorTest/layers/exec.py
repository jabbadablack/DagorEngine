"""exec layer: any command whose exit code is the result (0 passed, 77 skipped, anything else failed).

  target{ name:t="..."; layer:t="exec"
    command:t="{python} -m unittest discover -s tests"
    cwd:t="."                         // default: the test.blk dir
    jamfile:t="jamfile"               // optional: built (for the tested platform) before the command runs
    exe:t="../bin/foo"                // optional: a jam executable target; {exe} is its built file, name mangled
  }                                   //   by config and platform as in prog/_jBuild/defaults.jam

Placeholders in command and args: {python} (this interpreter), {engine} (engine root), {tools} (dagor_cdk tools dir),
{out} (the target's output dir: write extra result files there), {exe} (see above), {platform}, {arch}, {config}
(the tested build) and {host}, {hostArch} (the machine running the tests).
"""
import os
import shlex
import sys

from .. import jam, process
from ..model import Status, TargetResult, status_from_exit_code


def expand(arg: str, ctx, target) -> str:
  exe = ''
  if target.params.get('exe'):
    exe_path = target.path_param('exe')
    exe = os.path.join(os.path.dirname(exe_path), jam.mangled_exe_name(ctx, os.path.basename(exe_path)))
  return arg.format(python=sys.executable, engine=ctx.engine_root, tools=ctx.tools_dir, out=ctx.target_dir(target.id), exe=exe,
                    platform=ctx.platform, arch=ctx.arch, config=ctx.config, host=ctx.host, hostArch=ctx.host_arch)


def run(ctx, target, builds, env) -> TargetResult:
  res = TargetResult(id=target.id, layer=target.layer, tags=target.tags, status=Status.PASSED)
  if target.params.get('jamfile'):
    jamfile = target.path_param('jamfile')
    build = builds.ensure(jamfile)
    if build.exit_code != 0:
      res.status = Status.ERROR
      res.message = 'build failed ({}), see the build log'.format(build.describe_exit())
      res.log = ctx.rel(builds.log(jamfile))
      return res
  try:
    cmd = [expand(a, ctx, target) for a in shlex.split(target.params['command']) + target.args]
  except (KeyError, IndexError, ValueError) as e:
    res.status = Status.ERROR
    res.message = 'bad command {!r}: {}'.format(target.params['command'], e)
    return res
  log = os.path.join(ctx.target_dir(target.id), 'output.log')
  full_env = dict(os.environ)
  full_env.update(env)
  full_env['DAGOR_TEST_OUT'] = ctx.target_dir(target.id)
  timeout = target.timeout * ctx.timeout_scale
  pr = process.run(cmd, cwd=target.path_param('cwd', '.'), log_path=log, timeout=timeout, env=full_env)
  res.log = ctx.rel(log)
  res.duration = pr.duration
  res.exit_code = pr.exit_code
  if pr.timed_out:
    res.status = Status.TIMEOUT
    res.message = 'killed by the runner after {:.0f} s'.format(timeout)
  else:
    res.status = status_from_exit_code(pr.exit_code)
    if pr.exit_code is None:
      res.message = 'cannot start the command, see the log'
    elif res.status == Status.FAILED:
      res.message = 'command {}'.format(pr.describe_exit())
  return res
