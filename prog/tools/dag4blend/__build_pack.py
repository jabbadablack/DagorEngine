"""Build an installable add-on without modifying the source directory."""
import argparse
from pathlib import Path
import zipfile


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('target', nargs='?', choices=['FINAL'])
    parser.add_argument('--output', type=Path, help='Write a separate installation archive')
    args = parser.parse_args(argv)
    source = Path(__file__).resolve().parent
    destination = args.output
    if destination is None:
        destination = (source.parent.parent.parent / 'tools/dagor_cdk/universal/dag4blend.zip'
                       if args.target == 'FINAL' else source / 'dag4blend.zip')
    destination = destination.resolve()
    dependencies = source.parent / 'pythonCommon'
    entries = {}
    for path in sorted(source.rglob('*')):
        relative = path.relative_to(source)
        if not path.is_file() or any(part in {'additional', '__pycache__', 'tests', '.git'}
                                     for part in relative.parts):
            continue
        if path.suffix in {'.bak', '.blend1', '.zip', '.pyc', '.pyo'}:
            continue
        if path.name in {'__build_pack.py', 'pack.bat'}:
            continue
        entries['dag4blend/' + relative.as_posix()] = path
    for name in ('datablock.py', 'pyparsing.py'):
        path = dependencies / name
        if not path.is_file():
            raise FileNotFoundError(f'Missing packaging dependency: {path}')
        entries['dag4blend/' + name] = path
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(entries.items()):
            archive.write(path, name)
    print(f'Built {destination} ({len(entries)} files)')
    return destination


if __name__ == '__main__':
    main()
