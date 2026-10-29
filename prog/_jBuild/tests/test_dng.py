import contextlib
import importlib.util
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('dng', ROOT / 'dng.py')
dng = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dng)


class EntryPointTests(unittest.TestCase):
    def test_build_uses_cmake_from_the_engine_layout(self):
        with patch.object(dng, 'run') as run, patch.dict(os.environ):
            self.assertEqual(dng.main(['build', '--project', 'dag2blk']), 0)
        configure, build = [call.args[0] for call in run.call_args_list]
        self.assertEqual(configure[:3], ['cmake', '-S', ROOT / 'prog/_jBuild'])
        self.assertEqual(build, ['cmake', '--build', ROOT / '_output/cmake/dev', '--target', 'dag2blk'])

    def test_dry_run_new_does_not_create_a_directory(self):
        folder = ROOT / '_output/dng-dry-run-should-not-exist'
        self.assertFalse(folder.exists())
        with contextlib.redirect_stdout(io.StringIO()), patch.dict(os.environ):
            self.assertEqual(dng.main(['new', '--name', 'DryRunTest', '--directory', str(folder), '--dry-run']), 0)
        self.assertFalse(folder.exists())

    def test_only_one_root_python_entry_point(self):
        self.assertEqual([p.name for p in ROOT.glob('*.py')], ['dng.py'])


if __name__ == '__main__':
    unittest.main()
