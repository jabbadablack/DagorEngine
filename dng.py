#!/usr/bin/env python3
"""Bootstrap Dagor, build CMake workspaces, and create or run daNetGame projects."""
import argparse
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'prog/_jBuild'))
import ide


def run(command, cwd=ROOT, dry_run=False):
    print(f'[{cwd}] ' + subprocess.list2cmdline([str(x) for x in command]), flush=True)
    if not dry_run:
        subprocess.run([str(x) for x in command], cwd=cwd, check=True)


def environment(devtools):
    directory = Path(devtools).resolve()
    os.environ['GDEVTOOL'] = directory.as_posix()
    os.environ['PATH'] = str(directory) + os.pathsep + os.environ.get('PATH', '')


def configure(opts):
    source = Path(opts.directory).resolve() if opts.directory else ROOT / 'prog/_jBuild'
    if opts.build_dir:
        build = Path(opts.build_dir).resolve()
    elif opts.directory:
        build = source / '_output/cmake' / opts.config
    else:
        build = ROOT / '_output/cmake' / opts.config
    run(['cmake', '-S', source, '-B', build, '-G', 'Ninja',
         '-DPython3_EXECUTABLE=' + sys.executable, '-DDAGOR_ENGINE_ROOT=' + str(ROOT), '-DDAGOR_ACTIVE_PROJECT=' + opts.project,
         '-DDAGOR_CONFIG=' + opts.config, '-DDAGOR_PLATFORM=' + opts.platform,
         '-DDAGOR_ARCH=' + opts.arch, *(['-DDAGOR_JAM=' + opts.jam] if opts.jam else [])], dry_run=opts.dry_run)
    return build


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('bootstrap', 'configure', 'build', 'rebuild', 'clean',
        'new', 'list', 'run', 'editor', 'asset-viewer', 'ui-editor', 'content', 'tools', 'register', 'generate'))
    parser.add_argument('--project', default='dag2blk')
    parser.add_argument('--directory', help='Standalone game project root')
    parser.add_argument('--name')
    parser.add_argument('--template', choices=('singleplayer', 'multiplayer'), default='singleplayer')
    parser.add_argument('--config', choices=('dbg', 'dev', 'rel'), default='dev')
    parser.add_argument('--platform', choices=('windows', 'linux', 'macOS'), default=ide.host_platform())
    parser.add_argument('--arch', default='native')
    parser.add_argument('--jam')
    parser.add_argument('--server', action='store_true', help='Build/run a multiplayer dedicated server')
    parser.add_argument('--build-dir')
    parser.add_argument('--devtools', default=os.environ.get('GDEVTOOL', str(ROOT.parent / 'devtools')))
    parser.add_argument('--install-devtools', action='store_true', help='Download/configure host toolchain during bootstrap')
    parser.add_argument('--fetch-tools-data', action='store_true', help='Install official engine tool resources without sample assets')
    parser.add_argument('--skip-build', action='store_true', help='Configure only during bootstrap')
    parser.add_argument('--skip-intellisense', action='store_true')
    parser.add_argument('--no-engine-solution', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--add-engine-solution', action='store_true', help='Also register the game in the engine solution')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--components', nargs='+', choices=('shaders', 'assets', 'vromfs', 'gui'), default=['shaders', 'assets', 'vromfs', 'gui'])
    opts, extra = parser.parse_known_args(argv)
    if extra[:1] == ['--']: extra = extra[1:]
    if extra and opts.action not in ('run', 'editor', 'asset-viewer', 'ui-editor'):
        parser.error('Unexpected arguments: ' + ' '.join(extra))
    try:
        environment(opts.devtools)
        if opts.directory and opts.action != 'new':
            opts.project = ide.project_name(opts.directory)
            if not opts.dry_run: ide.register_project(opts.directory, opts.project)
        if opts.action == 'bootstrap':
            if opts.install_devtools or not Path(opts.devtools, 'jam.exe' if os.name == 'nt' else 'jam').exists():
                run([sys.executable, ROOT / 'prog/_jBuild/bootstrap/make_devtools.py', Path(opts.devtools).resolve()], dry_run=opts.dry_run)
            from game_project import ensure_tools_data
            ensure_tools_data(opts, run)
            build = configure(opts)
            if not opts.skip_build:
                run(['cmake', '--build', build, '--target', 'dagor_tools', opts.project], dry_run=opts.dry_run)
        elif opts.action == 'configure':
            configure(opts)
        elif opts.action in ('build', 'rebuild', 'clean'):
            build = configure(opts)
            target = opts.project + ('_server' if opts.server else '')
            if opts.action != 'build': target += '_' + opts.action
            run(['cmake', '--build', build, '--target', target], dry_run=opts.dry_run)
        elif opts.action == 'run' and opts.server:
            if not opts.directory: raise ValueError('Specify --directory for a standalone server')
            folder = Path(opts.directory).resolve()
            arch = ide.host_arch() if opts.arch == 'native' else opts.arch
            suffix = '' if opts.config == 'rel' else '-' + opts.config
            executable = folder / 'game' / (opts.platform + '-' + arch) / (opts.project + '-server' + suffix + ('.exe' if opts.platform == 'windows' else ''))
            run([executable, *extra], folder / 'game', opts.dry_run)
        elif opts.action == 'run':
            executable, directory = ide.runtime(opts)
            run([executable, *extra], directory, opts.dry_run)
        elif opts.action == 'new':
            if opts.dry_run:
                print('Would create ' + (opts.name or '<name>') + ' from ' + opts.template + ' in ' + (opts.directory or str(ROOT.parent)))
                return 0
            from create_game import create_game
            import json
            print(json.dumps(create_game(opts.name or '', opts.add_engine_solution and not opts.no_engine_solution, not opts.skip_intellisense,
                opts.platform, opts.arch, opts.directory, opts.template)))
        elif opts.action == 'tools':
            from game_project import build_tools
            build_tools(opts, run)
        elif opts.action == 'content':
            from game_project import build_content
            build_content(opts, run)
        elif opts.action in ('editor', 'asset-viewer', 'ui-editor'):
            from game_project import launch_tool
            launch_tool(opts, extra, run)
        else:
            if opts.dry_run and opts.action in ('register', 'generate'):
                print('Would ' + opts.action + ' ' + opts.project)
                return 0
            arguments = [opts.action, '--project', opts.project, '--platform', opts.platform,
                         '--arch', opts.arch, '--config', opts.config]
            if opts.directory: arguments += ['--directory', opts.directory]
            if opts.jam: arguments += ['--jam', opts.jam]
            if opts.dry_run: arguments += ['--dry-run']
            return ide.main(arguments + (['--', *extra] if extra else []))
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
