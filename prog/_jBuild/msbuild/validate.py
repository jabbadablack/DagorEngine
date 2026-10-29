"""Check the VS integration against installed MSBuild and the generated Jam caches."""
import argparse
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

from generate_projects import ROOT, PROJECTS, NS


def evaluate(msbuild, project, configuration, extra=()):
    run = subprocess.run([msbuild, str(project), '/nologo', '/nr:false',
                          f'/p:Configuration={configuration}', '/p:Platform=x64',
                          '/getProperty:ConfigurationType,PlatformToolset,ProjectRootDir,JamBuildCommandLine,LocalDebuggerCommand,NMakeIncludeSearchPath,NMakeForcedIncludes,NMakePreprocessorDefinitions',
                          '/getItem:ProjectCapability', *extra],
                         capture_output=True, text=True, check=True)
    return json.loads(run.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--msbuild', required=True)
    opts = parser.parse_args()
    for _, relative in PROJECTS:
        project = ROOT / relative
        files = ROOT / '_output' / 'visualstudio' / project.stem / 'files.props'
        nodes = ET.parse(files).getroot().findall('./*/*')
        assert nodes, f'Empty project file list: {project}'
        for node in nodes:
            file = node.get('Include')
            assert '*' not in file and ';' not in file and '$(' not in file
            assert (project.parent / file).exists(), file
        for config in ('dbg', 'dev', 'rel'):
            data = evaluate(opts.msbuild, project, config)
            props = data['Properties']
            capabilities = {i['Identity'] for i in data['Items']['ProjectCapability']}
            assert 'DagorProject' in capabilities, project
            assert props['ConfigurationType'] == 'Makefile'
            if project.stem == 'prog':
                assert 'DagorSharedProject' in capabilities
                continue
            command = props['JamBuildCommandLine']
            assert '-sPlatform=windows' in command and '-sPlatformArch=x86_64' in command
            assert f'-sConfig={config}' in command
            assert Path(props['LocalDebuggerCommand']).is_absolute(), props['LocalDebuggerCommand']
            assert 'X:' not in props['LocalDebuggerCommand']
            expected = ET.parse(ROOT / '_output' / 'visualstudio' / project.stem / config / 'intellisense.props').getroot()
            shared = evaluate(opts.msbuild, ROOT / 'prog' / 'prog.vcxproj', config,
                              [f"/p:ProjectRootDir={props['ProjectRootDir']}", f'/p:JamBuildCommandLine={command}'])['Properties']
            for name in ('NMakeIncludeSearchPath', 'NMakeForcedIncludes'):
                value = expected.find(f'./{{{NS}}}PropertyGroup/{{{NS}}}{name}').text or ''
                assert shared[name] == value, (project, config, name)
            database = json.loads((files.parent / config / 'compile_commands.json').read_text())
            assert database and Path(database[0]['arguments'][0]).exists()
        print(f'PASS {relative}: source visibility, all configurations, Jam/debugger paths, shared IntelliSense')


if __name__ == '__main__':
    main()
