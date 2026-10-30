"""Standalone project content and tool pipeline, independent of sample projects."""
import json
import os
import re
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]


def project_configuration(directory):
    application = Path(directory) / 'application.blk'
    if not application.is_file():
        return None
    text = application.read_text(encoding='utf-8')
    values = {}
    for key, field in (('name', 'projectName'), ('engine', 'engineRoot')):
        match = re.search(r'^' + field + r':t\s*=\s*("(?:\\.|[^"\\])*")', text, re.M)
        if match:
            values[key] = json.loads(match[1])
    return values if 'name' in values else None


def ensure_tools_data(opts, run):
    """Install only mandatory engine tool data, never sample content."""
    sentinel = ROOT / 'tools/dagor_cdk/commonData/fonts/roboto-regular.ttf'
    if sentinel.exists() and not opts.fetch_tools_data:
        return
    archive = ROOT / '_output/downloads/tools-base-2026.10.11.7z'
    extractor = shutil.which('7z') or (r'C:\Program Files\7-Zip\7z.exe' if os.name == 'nt' else '7z')
    if not opts.dry_run:
        from urllib.request import urlopen
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            partial = archive.with_suffix('.download')
            try:
                with urlopen('https://dagorenginedata.cdn.gaijin.net/head-2026.10.11/tools-base.7z', timeout=60) as response, partial.open('wb') as out:
                    shutil.copyfileobj(response, out)
                partial.replace(archive)
            finally:
                partial.unlink(missing_ok=True)
    # Skip existing files so bootstrap cannot replace local tool customizations.
    run([extractor, 'x', archive, '-o' + str(ROOT), '-aos', '-y'], ROOT, opts.dry_run)
def materialize(destination, name, multiplayer=False, engine=None):
    engine = Path(engine or ROOT)
    destination.mkdir(parents=True, exist_ok=False)
    for path in ('game', 'develop/levels/starter', 'develop/assets/primitives', 'tools'):
        (destination / path).mkdir(parents=True, exist_ok=True)
    from primitives import generate
    generate(destination / 'develop/assets/primitives')
    launchers(destination, engine, multiplayer)


def launchers(destination, engine, multiplayer):
    # Match the sample's develop entry points; F2/F10 are in-game controls.
    commands = {'dabuild': 'assets', 'daViewer': '--asset-viewer', 'daEditor': '--level-editor'}
    for name, args in commands.items():
        (destination / 'develop' / (name + '.cmd')).write_text(f'@echo off\npython "%~dp0..\\prog\\build.py" {args} %*\n')
        script = destination / 'develop' / (name + '.sh')
        script.write_text('#!/bin/sh\nset -eu\nproject_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)\n' +
            f'exec python3 "$project_dir/prog/build.py" {args} "$@"\n')
        script.chmod(0o755)


def project_directory(opts):
    if opts.directory:
        return Path(opts.directory).resolve()
    import ide
    return ide.projects(opts.platform)[opts.project][0].parent


def cdk(opts, program):
    import ide
    arch = ide.host_arch()
    suffix = '.exe' if ide.host_platform() == 'windows' else ''
    result = ROOT / 'tools/dagor_cdk' / f'{ide.host_platform()}-{arch}' / (program + suffix)
    if not result.is_file() and not opts.dry_run:
        raise RuntimeError(f'Missing {result}; run dng.py bootstrap to build the engine tools.')
    return result


def launch_tool(opts, extra, run):
    directory = project_directory(opts)
    if opts.action == 'editor':
        # daEditor resolves this argument relative to the workspace SDK folder.
        command = [cdk(opts, 'daEditor3x-dev'), directory / 'application.blk', 'levels/starter/starter.level.blk', *extra]
    elif opts.action == 'asset-viewer':
        command = [cdk(opts, 'assetViewer2-dev'), directory / 'application.blk', *extra]
    else:
        import ide, argparse
        runtime_opts = argparse.Namespace(project='dargbox', platform=ide.host_platform(), arch='native', config='dev')
        executable, working = ide.runtime(runtime_opts)
        if not executable.exists() and not opts.dry_run: raise RuntimeError('Build dargbox with dng.py bootstrap first')
        script = json.dumps((directory / 'prog/scripts/ui/main.nut').as_posix())
        run([executable, '-config:script:t=' + script, *extra], working, opts.dry_run)
        return
    run(command, directory / 'develop', opts.dry_run)


def build_content(opts, run):
    directory = project_directory(opts)
    if 'shaders' in opts.components:
        backend = {'windows': 'dx11', 'linux': 'spirv', 'macOS': 'metal'}[opts.platform]
        compiler = {'windows': 'dsc2-hlsl11-dev', 'linux': 'dsc2-spirv-dev', 'macOS': 'dsc2-metal-dev'}[opts.platform]
        for config in (f'shaders_{backend}.blk', 'shaders_tools11.blk' if opts.platform == 'windows' else f'shaders_tools_{backend}.blk'):
            if not (directory / 'prog/shaders' / config).exists():
                config = 'shaders_tools11.blk'
            extra = [] if opts.platform == 'windows' or not config.startswith('shaders_tools') else ['-out', directory / ('tools/toolsSpirV' if opts.platform == 'linux' else 'tools/toolsMTL')]
            run([cdk(opts, compiler), config, '-q', '-shaderOn', '-cj1', '-o', directory / '_output/shaders' / (backend + '-' + Path(config).stem), *extra], directory / 'prog/shaders', opts.dry_run)
        run([cdk(opts, 'dsc2-stub-dev'), 'shaders_tools_exp.blk', '-q', '-shaderOn', '-cj1', '-o', directory / '_output/shaders/export'], directory / 'prog/shaders', opts.dry_run)
    if 'assets' in opts.components:
        if not opts.dry_run and not list((directory / 'tools').glob('tools*.shdump.bin')):
            raise RuntimeError("Build this project's shaders before assets (python prog/build.py shaders).")
        run([cdk(opts, 'daBuild-dev'), directory / 'application.blk', '-q'], directory / 'develop', opts.dry_run)
    if 'gui' in opts.components:
        if not opts.dry_run: (directory / 'develop/gui/pc.out.ui').mkdir(parents=True, exist_ok=True)
        run([cdk(opts, 'fontgen2-dev'), 'fontgenPC.blk', '-fullDynamic', '-quiet'], directory / 'develop/gui/fonts', opts.dry_run)
        for config in ('fonts.vromfs.blk',):
            run([cdk(opts, 'vromfsPacker-dev'), config, '-quiet'], directory / 'develop/gui', opts.dry_run)
    if 'vromfs' in opts.components:
        run([cdk(opts, 'vromfsPacker-dev'), 'mk.vromfs.blk', '-quiet', '-addpath:.'], directory / 'prog', opts.dry_run)
    if 'levels' in opts.components:
        batch = directory / '_output/export-levels.dcmd'
        editor = cdk(opts, 'daEditor3x-dev')
        if not opts.dry_run:
            batch.parent.mkdir(parents=True, exist_ok=True)
            metadata = project_configuration(directory)
            (directory / 'game/content' / metadata['name'].lower() / 'levels').mkdir(parents=True, exist_ok=True)
            workspace = Path(os.path.relpath(directory / 'application.blk', editor.parent)).as_posix()
            batch.write_text('set_workspace "' + workspace + '" no\n' +
                'project.open levels/starter/starter.level.blk no no\nproject.export.pc starter.bin\n')
            batch.with_suffix('.dcmd.err').unlink(missing_ok=True)
        run([editor, batch, '-drv:stub', '-quiet', '-fatals_to_stderr'], directory / 'develop', opts.dry_run)
        if not opts.dry_run:
            output = directory / 'game/content' / metadata['name'].lower() / 'levels/starter.bin'
            if batch.with_suffix('.dcmd.err').exists() or not output.is_file():
                raise RuntimeError('daEditor level export failed; see ' + str(batch) + '.err')


def build_tools(opts, run):
    import ide
    platform = ide.host_platform()
    recipes = ['sceneTools/daEditorX/jamfile-editor', 'sceneTools/daEditorX/jamfile',
        'sceneTools/assetExp/jamfile', 'converters/ddsxCvt2/jamfile',
        'AssetViewer/jamfile', 'sceneTools/assetExp/ddsxConv/jamfile',
        'ShaderCompiler2/jamfile', 'ShaderCompiler2/jamfile-stub',
        'sceneTools/vromfsPacker/jamfile', 'FontGenerator/jamfile']
    arch = ide.host_arch() if opts.arch == 'native' else opts.arch
    for recipe in recipes:
        run([ide.jam_executable(opts.jam), '-sRoot=../..', '-sPlatform=' + platform,
             '-sPlatformArch=' + arch, '-sConfig=dev', '-f' + recipe], ROOT / 'prog/tools', opts.dry_run)
    run([ide.jam_executable(opts.jam), '-sPlatform=' + platform, '-sPlatformArch=' + arch, '-sConfig=dev'],
        ROOT / 'prog/tools/dargbox', opts.dry_run)

    gui = ROOT / 'prog/tools/sceneTools/guiShaders_commonData'
    compiler = cdk(opts, {'windows': 'dsc2-hlsl11-dev', 'linux': 'dsc2-spirv-dev', 'macOS': 'dsc2-metal-dev'}[platform])
    run([compiler, 'shaders_guiMinimal.blk', '-out', ROOT / 'tools/dagor_cdk/commonData/guiShaders', '-q', '-shaderOn', '-cj1', '-o', ROOT / '_output/shaders/tools-gui'], gui, opts.dry_run)
