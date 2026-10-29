"""Create standalone Dagor projects from the singleplayer/multiplayer templates."""
import argparse
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid
from xml.sax.saxutils import escape

from generate_projects import ROOT, PROJECTS, discover_projects, filters, main as regenerate, write_solution


def create_game(name, engine_solution=False, intellisense=True, portable_platform=None,
                portable_arch='native', directory=None, template_name='singleplayer'):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,63}', name):
        raise ValueError('Use 1-64 letters, digits or underscores, starting with a letter.')
    reserved = {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(1, 10)), *(f'LPT{i}' for i in range(1, 10))}
    if name.upper() in reserved:
        raise ValueError('That name is reserved by Windows.')
    if template_name not in ('singleplayer', 'multiplayer'):
        raise ValueError('Choose the singleplayer or multiplayer template.')
    if name.casefold() in {n.casefold() for n, _ in PROJECTS} or any(Path(p).stem.casefold() == name.casefold() for _, p in discover_projects()):
        raise ValueError('A project with that name is already registered with this engine.')
    destination = Path(directory or ROOT.parent / name).resolve()
    if destination.exists():
        raise ValueError(f'The project directory already exists: {destination}')
    prog = destination / 'prog'
    template = Path(__file__).resolve().parents[3] / 'templates' / template_name
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from game_project import materialize
    try:
        location = os.path.relpath(prog, ROOT).replace('\\', '/')
    except ValueError as error:
        raise ValueError('The engine and project must be on the same drive for Jam paths.') from error
    materialize(destination, name, template_name == 'multiplayer', ROOT)
    replacements = {'@GAME_NAME@': name, '@GAME_ID@': name.lower(), '@PROJECT_GUID@': '{' + str(uuid.uuid4()).upper() + '}',
                    '@ENGINE_ROOT@': ROOT.as_posix(), '@ENGINE_ROOT_XML@': escape(ROOT.as_posix()),
                    '@PROJECT_LOCATION@': location, '@ENGINE_FROM_PROG@': os.path.relpath(ROOT, prog).replace('\\', '/'), '@PROJECT_ROOT@': destination.as_posix()}
    from itertools import chain
    common = template.parent / 'common'
    for source in chain(common.rglob('*'), template.rglob('*')):
        if not source.is_file() or "__pycache__" in source.parts or source.suffix in (".pyc", ".pyo"):
            continue
        relative = source.relative_to(common if source.is_relative_to(common) else template)
        if relative == Path('prog/project.vcxproj'):
            relative = Path('prog') / f'{name}.vcxproj'
        relative = Path(str(relative).replace('@GAME_ID@', name.lower()).replace('@GAME_NAME@', name))
        target = destination / relative
        if source.suffix in ('.ttf', '.otf', '.dag'):
            import shutil
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        content = source.read_text(encoding='utf-8')
        for token, value in replacements.items():
            content = content.replace(token, value)
        target.write_text(content, encoding='utf-8')
    sys.path.insert(0, str(Path(__file__).parent.parent))
    project = prog / f'{name}.vcxproj'
    registry = ROOT / '_output' / 'ide' / 'project-registry.json'
    records = json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else []
    records.append({'name': name, 'project': str(project), 'template': template_name})
    registry.parent.mkdir(parents=True, exist_ok=True)
    registry.write_text(json.dumps(records, indent=2), encoding='utf-8')
    filters(project)
    write_solution(destination / f'{name}.sln', [(name, project)])
    if engine_solution:
        with redirect_stdout(sys.stderr):
            regenerate()
    if intellisense:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ide import host_platform, jam_executable
        target_platform = portable_platform or host_platform()
        if target_platform == 'windows' and portable_arch in ('native', 'x86_64'):
            for config in ('dev', 'dbg', 'rel'):
                subprocess.run([sys.executable, str(Path(__file__).with_name('intellisense.py')),
                                '--jam', jam_executable(), '--directory', str(prog), '--source-directory', str(prog),
                                '--output', str(ROOT / '_output/visualstudio' / name / config / 'intellisense.props'),
                                '--', '-sPlatform=windows', '-sPlatformArch=x86_64', f'-sConfig={config}'],
                               check=True, stdout=sys.stderr)
        else:
            subprocess.run([sys.executable, str(Path(__file__).parent.parent / 'ide.py'), 'generate',
                            '--project', name, '--platform', target_platform, '--arch', portable_arch,
                            '--output', str(ROOT / '_output/ide' / name)], check=True, stdout=sys.stderr)
    return {'name': name, 'directory': str(destination), 'project': str(project),
            'solution': str(destination / f'{name}.sln'), 'cmake': str(destination / 'CMakeLists.txt')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--directory')
    parser.add_argument('--template', choices=('singleplayer', 'multiplayer'), default='singleplayer')
    parser.add_argument('--no-engine-solution', action='store_true')
    parser.add_argument('--add-engine-solution', action='store_true')
    parser.add_argument('--skip-intellisense', action='store_true')
    opts = parser.parse_args()
    try:
        result = create_game(opts.name, opts.add_engine_solution and not opts.no_engine_solution, not opts.skip_intellisense,
                             directory=opts.directory, template_name=opts.template)
        print(json.dumps(result))
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
