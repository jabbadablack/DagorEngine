"""Recreate the solution and folder filters without editing engine project source lists."""
from pathlib import Path
import os
import json
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
PROJECTS = [
    ('testGI', 'samples/testGI/prog/testGI.vcxproj'),
    ('skiesSample', 'samples/skiesSample/prog/skiesSample.vcxproj'),
    ('dng_scene_viewer', 'samples/dngSceneViewer/prog/dng_scene_viewer.vcxproj'),
    ('outer_space', 'outerSpace/prog/outer_space.vcxproj'),
    ('ShaderCompiler2', 'prog/tools/ShaderCompiler2/ShaderCompiler2.vcxproj'),
    ('AssetViewer', 'prog/tools/AssetViewer/AssetViewer.vcxproj'),
    ('daEditorX', 'prog/tools/sceneTools/daEditorX/daEditorX.vcxproj'),
    ('dag2blk', 'prog/tools/converters/dag2blk/dag2blk.vcxproj'),
    ('dargbox', 'prog/tools/dargbox/dargbox.vcxproj'),
    ('Dagor Engine', 'prog/prog.vcxproj'),
]
NS = 'http://schemas.microsoft.com/developer/msbuild/2003'
ET.register_namespace('', NS)


def filters(project):
    xml = ET.parse(project).getroot()
    paths = {}
    for kind, item in [('ClCompile', 'CppSource'), ('ClInclude', 'CppHeader'),
                       ('None', 'bat'), ('None', 'DagorMisc')]:
        for node in xml.findall(f'.//{{{NS}}}{item}'):
            for pattern in node.get('Include').split(';'):
                for path in project.parent.glob(pattern.replace('\\', '/')):
                    if path.is_file():
                        paths[path.relative_to(project.parent)] = kind
    root = ET.Element(f'{{{NS}}}Project', ToolsVersion='4.0')
    folders = set()
    for path in paths:
        folders.update(p for p in path.parents if str(p) != '.')
    group = ET.SubElement(root, 'ItemGroup')
    for folder in sorted(folders):
        name = str(folder).replace('/', '\\')
        node = ET.SubElement(group, 'Filter', Include=name)
        ET.SubElement(node, 'UniqueIdentifier').text = '{' + str(uuid.uuid5(uuid.NAMESPACE_URL, name)).upper() + '}'
    group = ET.SubElement(root, 'ItemGroup')
    for path, kind in sorted(paths.items()):
        node = ET.SubElement(group, kind, Include=str(path).replace('/', '\\'))
        if str(path.parent) != '.':
            ET.SubElement(node, 'Filter').text = str(path.parent).replace('/', '\\')
    ET.indent(root)
    ET.ElementTree(root).write(str(project) + '.filters', encoding='utf-8', xml_declaration=True)
    # VC's editable project system requires literal items even when MSBuild can
    # evaluate wildcards. Keep expansion out of tracked source and IDE saves.
    items_root = ET.Element(f'{{{NS}}}Project')
    items = ET.SubElement(items_root, 'ItemGroup')
    for path, kind in sorted(paths.items()):
        ET.SubElement(items, kind, Include=str(path).replace('/', '\\'))
    ET.indent(items_root)
    destination = ROOT / '_output' / 'visualstudio' / project.stem / 'files.props'
    destination.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(items_root).write(destination, encoding='utf-8', xml_declaration=True)


def discover_projects():
    registry = ROOT / '_output' / 'ide' / 'project-registry.json'
    records = json.loads(registry.read_text(encoding='utf-8')) if registry.exists() else []
    external = [(record['name'], record['project']) for record in records if Path(record['project']).is_file()]
    builtin = [(name, path) for name, path in PROJECTS if (ROOT / path).is_file()]
    return [p for p in builtin if p[0] != 'Dagor Engine'] + sorted(external) + [p for p in builtin if p[0] == 'Dagor Engine']


def write_solution(destination, projects):
    lines = ['Microsoft Visual Studio Solution File, Format Version 12.00',
             '# Visual Studio Version 18', 'VisualStudioVersion = 18.0.0.0',
             'MinimumVisualStudioVersion = 17.0.0.0']
    guids = []
    for name, project in projects:
        guid = ET.parse(project).find(f'.//{{{NS}}}ProjectGuid').text.upper()
        guids.append(guid)
        path = os.path.relpath(project, destination.parent).replace('/', '\\')
        lines += [f'Project("{{8BC9CEB8-8B4A-11D0-8D11-00A0C91BC942}}") = "{name}", "{path}", "{guid}"', 'EndProject']
        filters(project)
    lines += ['Global', '\tGlobalSection(SolutionConfigurationPlatforms) = preSolution']
    for config in ('dev', 'dbg', 'rel'):
        lines.append(f'\t\t{config}|x64 = {config}|x64')
    lines += ['\tEndGlobalSection', '\tGlobalSection(ProjectConfigurationPlatforms) = postSolution']
    for config in ('dev', 'dbg', 'rel'):
        for guid in guids:
            lines.append(f'\t\t{guid}.{config}|x64.ActiveCfg = {config}|x64')
        # Build Solution builds one sample by default. Other executables are built explicitly.
        lines.append(f'\t\t{guids[0]}.{config}|x64.Build.0 = {config}|x64')
    lines += ['\tEndGlobalSection', 'EndGlobal']
    destination.write_text('\n'.join(lines) + '\n', encoding='utf-8-sig')


def main():
    write_solution(ROOT / 'DagorEngine.sln', [(name, ROOT / path) for name, path in discover_projects()])
    print('Generated DagorEngine.sln and project folder filters')


if __name__ == '__main__':
    main()
