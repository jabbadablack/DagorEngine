"""Generate VS IntelliSense settings and compile selected files using actual Jam flags."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET


def commands_from_jam(jam, directory, arguments):
    run = subprocess.run([jam, *arguments, '-sDumpBuildCmds=yes', '-d0', '-a', '-n'],
                         cwd=directory, capture_output=True, text=True, errors='replace')
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    # Jam may print setup diagnostics before the JSON array.
    start = run.stdout.find('[ ')
    if start < 0:
        raise RuntimeError('Jam did not produce a compilation database:\n' + run.stdout)
    data, _ = json.JSONDecoder().raw_decode(run.stdout[start:])
    return [entry for entry in data if entry.get('file') and entry.get('arguments')]


def settings(entry):
    includes, defines, forced = [], [], []
    args = iter(entry['arguments'][1:])
    for arg in args:
        if arg in ('-I', '/I', '-imsvc', '-isystem'):
            includes.append(next(args))
        elif arg.startswith(('-I', '/I')):
            includes.append(arg[2:])
        elif arg.startswith(('-D', '/D')):
            defines.append(arg[2:] if len(arg) > 2 else next(args))
        elif arg.startswith(('-FI', '/FI')):
            forced.append(arg[3:] if len(arg) > 3 else next(args))
    includes = [str((Path(entry['directory']) / value).resolve()) for value in includes]
    return includes, defines, forced


def compile_selected(entries, source, selection):
    selected = {os.path.normcase(str((source / f).resolve())) for f in selection.split(';') if f}
    matched = set()
    for entry in entries:
        file = os.path.normcase(str(Path(entry['file']).resolve()))
        if file not in selected:
            continue
        matched.add(file)
        Path(entry['output']).parent.mkdir(parents=True, exist_ok=True)
        # Jam stores the source/output outside arguments and leaves a trailing empty argument.
        command = [a for a in entry['arguments'] if a]
        command.extend([entry['file'], '/Fo' + entry['output']])
        print('Compiling ' + entry['file'], flush=True)
        subprocess.run(command, cwd=entry['directory'], check=True)
    if selected - matched:
        raise RuntimeError('No Jam compile command for: ' + ', '.join(sorted(selected - matched)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jam', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--source-directory', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--compile')
    parser.add_argument('arguments', nargs=argparse.REMAINDER)
    opts = parser.parse_args()
    arguments = opts.arguments[1:] if opts.arguments[:1] == ['--'] else opts.arguments
    entries = commands_from_jam(opts.jam, opts.directory, arguments)
    if not entries:
        raise RuntimeError('Jam returned no compilation commands')
    source = Path(opts.source_directory).resolve()
    if opts.compile is not None:
        if not opts.compile:
            raise RuntimeError('Select at least one C/C++ source file to compile')
        compile_selected(entries, source, opts.compile)
        return
    representative = next((e for e in entries if Path(e['file']).is_relative_to(source)), entries[0])
    includes, defines, forced = settings(representative)
    ns = 'http://schemas.microsoft.com/developer/msbuild/2003'
    ET.register_namespace('', ns)
    root = ET.Element(f'{{{ns}}}Project')
    group = ET.SubElement(root, 'PropertyGroup')
    for name, values in [('NMakeIncludeSearchPath', includes),
                         ('NMakePreprocessorDefinitions', defines), ('NMakeForcedIncludes', forced)]:
        # Escape MSBuild-special characters in compiler values before writing XML.
        value = ';'.join(v.replace('%', '%25').replace('$', '%24').replace(';', '%3B') for v in values)
        ET.SubElement(group, name).text = value
    output = Path(opts.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    ET.indent(root)
    ET.ElementTree(root).write(output, encoding='utf-8', xml_declaration=True)
    # The installed Visual Dagor extension propagates only these three properties:
    # ProjectRootDir, JamBuildCommandLine and NMakePreprocessorDefinitions. Match
    # the first two to provide the shared project with the same include context.
    shared = output.parents[2] / 'shared-intellisense.props'
    shared_root = ET.parse(shared).getroot() if shared.exists() else ET.Element(f'{{{ns}}}Project')
    label = output.parent.parent.name + '-' + output.parent.name
    for old in list(shared_root):
        if old.get('Label') == label:
            shared_root.remove(old)
    workdir = str(Path(opts.directory).resolve()) + os.sep
    conditions = [f"'$(ProjectRootDir)' == '{workdir}'"]
    for arg in arguments:
        if arg.startswith(('-sConfig=', '-f')):
            conditions.append(f"$(JamBuildCommandLine.Contains('{arg}'))")
    shared_group = ET.SubElement(shared_root, f'{{{ns}}}PropertyGroup', Label=label,
                                Condition=' and '.join(conditions))
    for element in group:
        if element.tag == 'NMakePreprocessorDefinitions':
            continue
        ET.SubElement(shared_group, f'{{{ns}}}{element.tag}').text = element.text
    ET.indent(shared_root)
    ET.ElementTree(shared_root).write(shared, encoding='utf-8', xml_declaration=True)
    output.with_name('compile_commands.json').write_text(json.dumps(entries, indent=2), encoding='utf-8')
    print(f'Wrote {len(entries)} Jam compilation commands and {output}')


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError, ValueError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
