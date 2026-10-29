"""Portable IDE workspace and Jam build entry point (Windows, Linux, macOS)."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).with_name('msbuild')))
from generate_projects import ROOT, discover_projects, PROJECTS
from intellisense import commands_from_jam, settings


def host_platform():
    return {'Windows': 'windows', 'Linux': 'linux', 'Darwin': 'macOS'}[platform.system()]


def host_arch():
    machine = platform.machine().lower()
    return {'amd64': 'x86_64', 'aarch64': 'arm64'}.get(machine, machine)


def projects(target_platform):
    result = {}
    for name, relative in discover_projects():
        if name == 'Dagor Engine':
            continue
        # The supplied shader-compiler project specifically targets DirectX 12.
        if name == 'ShaderCompiler2' and target_platform != 'windows':
            continue
        directory = (ROOT / relative).parent
        args = []
        if name in ('ShaderCompiler2', 'AssetViewer', 'daEditorX'):
            directory = ROOT / 'prog' / 'tools'
            jamfile = {'ShaderCompiler2': 'ShaderCompiler2/jamfile-dx12',
                       'AssetViewer': 'AssetViewer/jamfile', 'daEditorX': 'sceneTools/daEditorX/jamfile'}[name]
            args = ['-sRoot=../..', '-f' + jamfile]
        if name == 'dag2blk':
            args = ['-sPlatformSpec=clang']
        result[name] = (directory, args)
    return result


def jam_executable(explicit=None):
    if explicit:
        return explicit
    tools = Path(os.environ.get('GDEVTOOL', ROOT.parent / 'devtools'))
    candidate = tools / ('jam.exe' if os.name == 'nt' else 'jam')
    found = str(candidate) if candidate.exists() else shutil.which('jam')
    if not found:
        raise RuntimeError('Jam was not found. Run the engine devtools setup or pass --jam.')
    return found


def invocation(opts):
    registry = projects(opts.platform)
    if opts.project not in registry:
        raise ValueError('Unknown/unsupported project. Choices: ' + ', '.join(registry))
    directory, extra = registry[opts.project]
    if opts.project not in {n for n, _ in PROJECTS}:
        write_engine_header(directory.parent)
        extra = [*extra, '-sRoot=' + ROOT.as_posix(), '-sLocation=' + os.path.relpath(directory, ROOT).replace('\\', '/')]
    arch = host_arch() if opts.arch == 'native' else opts.arch
    args = [f'-sPlatform={opts.platform}', f'-sPlatformArch={arch}', f'-sConfig={opts.config}', *extra]
    return jam_executable(opts.jam), directory, args


def runtime(opts):
    if opts.project not in projects(opts.platform):
        raise ValueError('Unknown/unsupported project: ' + opts.project)
    arch = host_arch() if opts.arch == 'native' else opts.arch
    suffix = '' if opts.config == 'rel' else '-' + opts.config
    extension = '.exe' if opts.platform == 'windows' else ''
    name = opts.project
    if name in ('testGI', 'skiesSample'):
        directory = ROOT / 'samples' / name / 'game'
        filename = f'{name}-{opts.platform}-{arch}{suffix}{extension}'
        if opts.platform == 'macOS':
            bundle = 'testGI' if name == 'testGI' else 'SkiesSample'
            return directory / f'{bundle}.app/Contents/MacOS' / filename, directory
    elif name in ('outer_space', 'dng_scene_viewer'):
        directory = ROOT / ('outerSpace/game' if name == 'outer_space' else 'samples/dngSceneViewer/viewer')
        if opts.platform == 'macOS' and name == 'dng_scene_viewer':
            folder = (directory.parent / 'rel-build' if opts.config == 'rel' else directory) / f'DngSceneViewer-{arch}.app/Contents/MacOS'
            return folder / f'{name}{suffix}{extension}', directory
        return directory / f'{opts.platform}-{arch}' / f'{name}{suffix}{extension}', directory
    elif name == 'dargbox':
        directory = ROOT / 'tools' / 'dargbox'
        if opts.platform == 'macOS':
            return directory / f'dargbox-{arch}.app/Contents/MacOS' / f'dargbox{suffix}', directory
        return directory / f'{opts.platform}-{arch}' / f'dargbox{suffix}{extension}', directory
    elif name == 'dag2blk':
        directory = ROOT / 'tools' / 'converters' / 'dag2blk'
        filename = f'dag2blk{suffix}{extension}'
    elif name in ('AssetViewer', 'daEditorX', 'ShaderCompiler2'):
        directory = ROOT / 'tools' / 'dagor_cdk' / f'{opts.platform}-{arch}'
        filename = {'AssetViewer': 'assetViewer2', 'daEditorX': 'daEditor3x', 'ShaderCompiler2': 'dsc2-dx12'}[name] + suffix + extension
    else:
        project = next(Path(p) for n, p in discover_projects() if n == name)
        directory = project.parent.parent / 'game'
        return directory / f'{opts.platform}-{arch}' / f'{name}{suffix}{extension}', directory
    return directory / filename, directory


def cmake_value(value):
    return '[==[' + str(value).replace('\\', '/') + ']==]'


def write_engine_header(directory):
    header = Path(directory) / 'prog/engine_paths.h'
    content = '#pragma once\n#define DAGOR_EDITOR_SHADER_PREFIX ' + json.dumps((ROOT / 'samples/testGI/game/compiledShaders/game').as_posix()) + '\n'
    if not header.exists() or header.read_text(encoding='utf-8') != content:
        header.write_text(content, encoding='utf-8')


def register_project(directory, name=None):
    folder = Path(directory).resolve()
    candidates = list((folder / 'prog').glob('*.vcxproj'))
    if len(candidates) != 1:
        raise ValueError('Expected one project under the selected directory/prog.')
    project = candidates[0]
    write_engine_header(folder)
    name = name or project.stem
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', name) or name != project.stem:
        raise ValueError('Project name must match its vcxproj filename.')
    if name.casefold() in {n.casefold() for n, _ in PROJECTS}:
        raise ValueError('That name belongs to an engine project.')
    registry = ROOT / '_output/ide/project-registry.json'
    records = json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else []
    for record in records:
        if record['name'].casefold() == name.casefold():
            if Path(record['project']).resolve() != project:
                raise ValueError('Another project is already registered with that name.')
            return
    records.append({'name': name, 'project': str(project)})
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(records, indent=2), encoding='utf-8')


def generate(opts):
    jam, directory, args = invocation(opts)
    entries = commands_from_jam(jam, directory, args)
    if not entries:
        raise RuntimeError('Jam returned no compiler commands.')
    output = Path(opts.output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Jam leaves the source and output outside its arguments array. A standard
    # compilation database must include them in the executable command.
    for entry in entries:
        arguments = [a for a in entry['arguments'] if a]
        is_cl = Path(arguments[0]).name.lower() in ('cl.exe', 'clang-cl.exe', 'clang-cl')
        entry['arguments'] = arguments + [entry['file']] + (['/Fo' + entry['output']] if is_cl else ['-o', entry['output']])
    (output / 'compile_commands.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
    source_dir = (ROOT / next(p for n, p in discover_projects() if n == opts.project)).parent
    representative = next((e for e in entries if Path(e['file']).is_relative_to(source_dir)), entries[0])
    includes, defines, forced = settings(representative)
    executable, workdir = runtime(opts)
    variables = {
        'DAGOR_COMPILER': [entries[0]['arguments'][0]],
        'DAGOR_JAMFILE': [directory / next((a[2:] for a in args if a.startswith('-f')), 'jamfile')],
        'DAGOR_INDEX_SOURCES': sorted({e['file'] for e in entries if Path(e['file']).exists()}),
        'DAGOR_INDEX_INCLUDES': includes, 'DAGOR_INDEX_DEFINES': defines,
        'DAGOR_INDEX_FORCED': forced, 'DAGOR_PROJECT_NAMES': list(projects(opts.platform)),
        'DAGOR_EXECUTABLE': [executable], 'DAGOR_WORKING_DIRECTORY': [workdir],
    }
    lines = [f'set({key}\n' + '\n'.join('  ' + cmake_value(value) for value in values) + '\n)' for key, values in variables.items()]
    (output / 'dagor-model.cmake').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Generated {len(entries)} compiler commands for {opts.project} ({opts.platform}/{opts.arch}/{opts.config})')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('list', 'generate', 'build', 'rebuild', 'clean', 'run', 'new', 'register'))
    parser.add_argument('--project', default='testGI')
    parser.add_argument('--config', choices=('dbg', 'dev', 'rel'), default='dev')
    parser.add_argument('--platform', choices=('windows', 'linux', 'macOS'), default=host_platform())
    parser.add_argument('--arch', default='native')
    parser.add_argument('--jam')
    parser.add_argument('--output', default=str(ROOT / '_output' / 'ide'))
    parser.add_argument('--name')
    parser.add_argument('--directory')
    parser.add_argument('--template', choices=('singleplayer', 'multiplayer'), default='singleplayer')
    parser.add_argument('--dry-run', action='store_true')
    opts, extra = parser.parse_known_args()
    if extra[:1] == ['--']:
        extra = extra[1:]
    if extra and opts.action not in ('build', 'rebuild', 'clean', 'run'):
        parser.error('Unexpected arguments: ' + ' '.join(extra))
    try:
        if opts.action == 'list':
            print('\n'.join(projects(opts.platform)))
        elif opts.action == 'register':
            if not opts.directory:
                raise ValueError('Specify the standalone project directory with --directory.')
            register_project(opts.directory, opts.name)
        elif opts.action == 'new':
            from create_game import create_game
            print(json.dumps(create_game(opts.name or '', portable_platform=opts.platform, portable_arch=opts.arch,
                                         directory=opts.directory, template_name=opts.template)))
        elif opts.action == 'generate':
            generate(opts)
        elif opts.action == 'run':
            executable, directory = runtime(opts)
            if not executable.exists():
                raise RuntimeError(f'Executable not found: {executable}. Build the project first.')
            return subprocess.run([str(executable), *extra], cwd=directory).returncode
        else:
            jam, directory, args = invocation(opts)
            if opts.action == 'rebuild': args.append('-a')
            if opts.action == 'clean': args.append('clean')
            if opts.dry_run: args.append('-n')
            return subprocess.run([jam, *args, *extra], cwd=directory).returncode
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
