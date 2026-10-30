#!/usr/bin/env python3
"""Build this game's code and content from its own project directory."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

PROJECT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('components', nargs='*', choices=('code', 'shaders', 'assets', 'gui', 'vromfs', 'levels'))
    parser.add_argument('--config', choices=('dbg', 'dev', 'rel'), default='dev')
    parser.add_argument('--platform', choices=('windows', 'linux', 'macOS'))
    parser.add_argument('--arch', default='native')
    parser.add_argument('--server', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--level-editor', action='store_true')
    parser.add_argument('--asset-viewer', action='store_true')
    parser.add_argument('--clean', action='store_true')
    parser.add_argument('--configure-only', action='store_true')
    parser.add_argument('--no-build', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    arguments = sys.argv[1:]
    extra = []
    if '--' in arguments:
        separator = arguments.index('--')
        arguments, extra = arguments[:separator], arguments[separator + 1:]
    opts, unknown = parser.parse_known_args(arguments)
    extra = unknown + extra
    metadata = json.loads((PROJECT / 'dng-project.json').read_text())
    engine = Path(os.environ.get('DAGOR_ENGINE_ROOT', metadata['engine'])).resolve()
    if not (engine / 'prog/_jBuild/ide.py').exists():
        parser.error('Set DAGOR_ENGINE_ROOT to your engine checkout.')
    sys.path.insert(0, str(engine / 'prog/_jBuild'))
    import ide
    import game_project
    opts.platform = opts.platform or ide.host_platform()
    opts.directory, opts.project, opts.jam = str(PROJECT), metadata['name'], None
    os.environ['DAGOR_ENGINE_ROOT'] = str(engine)
    devtools = Path(os.environ.get('GDEVTOOL', engine.parent / 'devtools'))
    os.environ['PATH'] = str(devtools) + os.pathsep + os.environ.get('PATH', '')

    def run(command, cwd=PROJECT, dry_run=False):
        print(f'[{cwd}] ' + subprocess.list2cmdline([str(x) for x in command]), flush=True)
        if not (opts.dry_run or dry_run):
            subprocess.run([str(x) for x in command], cwd=cwd, check=True)

    try:
        if not opts.dry_run: ide.register_project(PROJECT, opts.project)
        tool = 'editor' if opts.level_editor else 'asset-viewer' if opts.asset_viewer else None
        if tool:
            opts.action = tool
            game_project.launch_tool(opts, extra, run)
            return 0
        components = ['code'] if opts.clean else [] if opts.no_build else opts.components or ['code', 'shaders', 'assets', 'gui', 'vromfs', 'levels']
        build = PROJECT / '_output/cmake' / opts.config
        if 'code' in components or opts.configure_only or opts.clean:
            run(['cmake', '-S', PROJECT, '-B', build, '-G', 'Ninja',
                '-DPython3_EXECUTABLE=' + sys.executable, '-DDAGOR_ENGINE_ROOT=' + str(engine), '-DDAGOR_CONFIG=' + opts.config,
                '-DDAGOR_PLATFORM=' + opts.platform, '-DDAGOR_ARCH=' + opts.arch])
            if not opts.configure_only:
                target = opts.project + ('_server' if opts.server else '') + ('_clean' if opts.clean else '_code')
                run(['cmake', '--build', build, '--target', target])
        opts.components = [c for c in components if c != 'code']
        if opts.components and not opts.configure_only:
            game_project.build_content(opts, run)
        if opts.run:
            executable, working = ide.runtime(opts)
            if opts.server:
                suffix = '' if opts.config == 'rel' else '-' + opts.config
                executable = executable.with_name(opts.project + '-server' + suffix + executable.suffix)
            run([executable, *extra], working)
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
