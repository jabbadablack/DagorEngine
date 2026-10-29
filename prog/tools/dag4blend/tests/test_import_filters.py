"""Pure Python discovery tests: related variants and wildcard/regex batches."""
import ast
from fnmatch import fnmatch
import os
from os import listdir
from os.path import abspath, basename, dirname, isfile, join
from pathlib import Path
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
tree = ast.parse((ROOT / 'importer/importer.py').read_text())
cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'DagImporter')
cls.bases = []
cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef)
            and node.name in {'filename_to_regex', 'file_to_filepaths', 'includes_to_filepaths', 'regex_to_filepaths'}]
exec(compile(ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[])), '<import filters>', 'exec'))
importer = DagImporter()
with tempfile.TemporaryDirectory(prefix='dagor-filter-test-', dir=ROOT / 'tests') as directory:
    directory = Path(directory)
    assert directory.resolve().is_relative_to(ROOT / 'tests')
    names = ['asset[1].lod02.dag', 'asset[1].lod01.DAG', 'asset[1]_dmg.lod02.dag',
             'asset[1]_dp_01.lod02.dag', 'asset[1]_dp_01_dmg_destr.lod00.dag',
             'asset[1]_destr.lod00.dag', 'asset[1]_destr.lod02.dag',
             'asset1.lod02.dag', 'ignore.txt']
    for name in names:
        (directory / name).write_bytes(b'')
    importer.filepath = str(directory / names[0])
    importer.with_lods = False
    importer.with_dps = importer.with_dmgs = importer.with_destr = True
    importer.with_dm = importer.check_subdirs = False
    discovered = importer.file_to_filepaths()
    selected = {Path(path).name for path in discovered}
    assert selected == {names[0], names[2], names[3], names[4], names[5]}, selected
    assert discovered[0] == importer.filepath
    importer.with_lods = True
    selected = {Path(path).name for path in importer.file_to_filepaths()}
    assert names[1] in selected and names[6] not in selected and names[7] not in selected
    importer.dirpath = str(directory)
    importer.includes, importer.excludes = 'asset*', '*_dmg*;*_destr*'
    files = importer.includes_to_filepaths()
    assert all(path.lower().endswith('.dag') for path in files)
    assert names[2] not in {Path(path).name for path in files}
    child = directory / 'child'
    child.mkdir()
    (child / 'asset_child.dag').write_bytes(b'')
    importer.check_subdirs = True
    assert str(child / 'asset_child.dag') in importer.includes_to_filepaths()
    importer.includes_re, importer.excludes_re = r'^asset.*\.dag$', r'_child'
    assert str(child / 'asset_child.dag') not in importer.regex_to_filepaths()
print('PASS: escaped filenames, LOD/DP/DMG variants, destruction LOD00, case-insensitive related import, wildcard stems, non-DAG exclusion, recursion')
