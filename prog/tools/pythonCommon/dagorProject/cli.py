"""Commands of a project's project.py (the project passes itself in, see templates/*/project.py)."""
import argparse
import os
import subprocess
import sys

from . import engine, glue
from .engine import ProjectError
from .glue import Project

EPILOG = '''examples:
  python project.py setup                  regenerate the engine glue after changing prog/danetgamelibs.txt
  python project.py relink ../DagorEngine  build with another engine checkout
  python project.py build                  code, shaders and vromfs (python project.py build code builds only code)
  python project.py test --layer ecs       build and run the project tests (any test_all.py run option)'''


def make_parser(project: Project):
  p = argparse.ArgumentParser(prog='project.py', description='Commands of the {} project.'.format(project.codename),
                              epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
  sub = p.add_subparsers(dest='command', required=True)
  sub.add_parser('setup', help='write the generated files that connect the project to its engine (prog/_engine.jam, '
                 '_engine.cmd/.sh, prog/_libs*)')
  r = sub.add_parser('relink', help='point engine.blk at another engine checkout, then setup')
  r.add_argument('engine_dir')
  r.add_argument('--absolute', action='store_true', help='store an absolute path (default: relative to the project, '
                 'absolute only across drives)')
  # build and test pass every following argument on (see PASS_THROUGH in main)
  sub.add_parser('build', help='setup, then prog/build.py with the given arguments: components (default: all, e.g. code '
                 'shaders vromfs assets), arch:<arch>, --dry-run')
  sub.add_parser('test', help='build and run the project tests: "test_all.py run --project <this project> --no-engine" of '
                 'the engine with the given arguments (python project.py test -h lists them)')
  sub.add_parser('info', help='print the engine and project paths')
  return p


def _run(cmd, cwd):
  print('--- Running: {}  in  {}'.format(' '.join(cmd), cwd), flush=True)
  return subprocess.call(cmd, cwd=cwd)


PASS_THROUGH = ('build', 'test')


def main(project: Project, argv):
  if argv and argv[0] in PASS_THROUGH:
    args = argparse.Namespace(command=argv[0], args=argv[1:])
  else:
    args = make_parser(project).parse_args(argv)
  try:
    if args.command == 'setup':
      glue.setup(project, verbose=True)
      return 0
    if args.command == 'relink':
      engine.write_engine_blk(project.root, os.path.abspath(args.engine_dir), absolute=args.absolute)
      glue.setup(project, verbose=True)
      return 0
    if args.command == 'info':
      print('project: {}\ncodename: {}\nengine: {}'.format(project.root, project.codename, project.engine_root()))
      return 0
    if args.command == 'build':
      glue.setup(project)
      return _run([sys.executable, 'build.py'] + args.args, cwd=project.prog)
    if args.command == 'test':
      engine_root = project.engine_root()
      return _run([sys.executable, os.path.join(engine_root, 'test_all.py'), 'run', '--project', project.root, '--no-engine']
                  + args.args, cwd=engine_root)
  except ProjectError as e:
    print('ERROR: {}'.format(e), file=sys.stderr)
    return 2
  return 2
