"""dng.py build: the engine tools (cdk), dargbox, the project template and, when named, the samples."""
import argparse
import os
import sys

from . import COMPONENTS, ENGINE_ROOT, HOST, Build, sync_tools_data

# id: (dir with its build.py, content dir that is not in git, archive with that content, built by default)
PROJECTS = {
  'cdk': (None, None, None, True),
  'dargbox': ('prog/tools/dargbox', None, None, True),
  'dngEmpty': ('templates/dng-empty/prog', None, None, True),
  'physTest': ('prog/samples/physTest', 'samples/physTest', 'samples-base.7z', False),
  'skiesSample': ('samples/skiesSample/prog', 'samples/skiesSample/develop', 'samples-base.7z', False),
  'testGI': ('samples/testGI/prog', 'samples/testGI/develop', 'samples-base.7z', False),
  'outerSpace': ('outerSpace/prog', 'outerSpace/develop', 'outerSpace-devsrc.7z', False),
  'dngSceneViewer': ('samples/dngSceneViewer/prog', 'samples/dngSceneViewer/viewer/content', 'dngSceneViewer.7z', False),
}
SAMPLES = [p for p, (_, content, _, _) in PROJECTS.items() if content]

EPILOG = '''examples:
  python dng.py build                       the engine tools, dargbox and the project template
  python dng.py build cdk -c code           only the engine tools
  python dng.py build samples               the samples whose content is unpacked (see README.md)
  python dng.py build outerSpace -c code -c shaders --arch x86_64'''


def make_parser():
  p = argparse.ArgumentParser(prog='dng.py build', description=__doc__, epilog=EPILOG,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('projects', nargs='*', metavar='PROJECT',
                 help='{} or samples (default: {})'.format(', '.join(PROJECTS), ' '.join(p for p in PROJECTS if PROJECTS[p][3])))
  p.add_argument('-c', '--component', action='append', default=[], metavar='COMPONENT',
                 help='{}, repeatable or comma separated (default: everything each project builds)'.format(', '.join(COMPONENTS)))
  p.add_argument('--arch', default='', help='target architecture, e.g. x86_64, arm64 (default: the host\'s)')
  p.add_argument('--dry-run', action='store_true', help='print the commands instead of running them')
  p.add_argument('--list', action='store_true', help='list the projects and whether their content is present')
  return p


def _build_cdk(b):
  cmd = {'windows': 'build_dagor_cdk_mini.cmd', 'macOS': './build_dagor_cdk_mini_macOS.sh',
         'linux': './build_dagor_cdk_mini_linux.sh'}[HOST]
  if b.arch and HOST != 'linux':
    cmd += ' ' + b.arch
  cwd = os.path.join(ENGINE_ROOT, 'prog', 'tools')
  if b.run(cmd, cwd):
    return True
  if HOST != 'windows':
    return False
  print('"{}" failed, trying once more'.format(cmd), flush=True)
  return b.run(cmd, cwd)


def main(argv):
  args = make_parser().parse_args(argv)
  if args.list:
    for p, (_, content, archive, default) in PROJECTS.items():
      state = '' if not content else ' (content: {})'.format(
        'present' if os.path.isdir(os.path.join(ENGINE_ROOT, content)) else 'missing, unpack ' + archive)
      print('{:16}{}{}'.format(p, 'default' if default else 'sample', state))
    return 0
  components = [c for a in args.component for c in a.split(',') if c]
  for c in components:
    if c not in COMPONENTS:
      make_parser().error('unknown component "{}", expected {}'.format(c, ', '.join(COMPONENTS)))
  for p in args.projects:
    if p not in PROJECTS and p != 'samples':
      make_parser().error('unknown project "{}", expected {} or samples'.format(p, ', '.join(PROJECTS)))
  named = {s for p in args.projects for s in (SAMPLES if p == 'samples' else [p])}
  projects = [p for p in PROJECTS if (p in named if named else PROJECTS[p][3])]

  sync_tools_data(args.dry_run)  # data of the engine tools that is not built
  b = Build(components, args.arch, args.dry_run)
  runner = Build(None)  # a project's build.py does its own dry run
  failed = []
  for p in projects:
    build_dir, content, archive, _ = PROJECTS[p]
    if content and not os.path.isdir(os.path.join(ENGINE_ROOT, content)):
      print('skipping {}: {} not found (unpack {} into the engine root, see README.md)'.format(p, content, archive), flush=True)
      continue
    if p == 'cdk':
      if components and 'code' not in components:
        continue
      if not _build_cdk(b):
        print('ERROR: building the engine tools failed, stopping', flush=True)
        return 1
      continue
    cmd = [sys.executable, 'build.py'] + components + (['arch:' + args.arch] if args.arch else [])
    if not runner.run(cmd + (['--dry-run'] if args.dry_run else []), os.path.normpath(os.path.join(ENGINE_ROOT, build_dir))):
      failed.append(p)
  if failed:
    print('ERROR: failed to build {}'.format(', '.join(failed)), flush=True)
  return 1 if failed else 0
