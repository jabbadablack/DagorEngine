import argparse
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ide
import create_game
import generate_projects


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        test_root = ide.ROOT / '_output' / 'ide-tests'
        test_root.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=test_root)
        assert Path(self.temp.name).resolve().is_relative_to(test_root.resolve())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for module in (ide, create_game, generate_projects):
            patcher = patch.object(module, 'ROOT', self.root)
            patcher.start()
            self.addCleanup(patcher.stop)
        shared = self.root / 'prog' / 'prog.vcxproj'
        shared.parent.mkdir(parents=True)
        shared.write_text('<Project xmlns="http://schemas.microsoft.com/developer/msbuild/2003"><PropertyGroup><ProjectGuid>{89D18E89-8553-4D5B-842E-EE8D4F78043F}</ProjectGuid></PropertyGroup></Project>')

    def options(self, **values):
        opts = dict(project='dag2blk', platform='windows', arch='x86_64', config='dev', jam='jam', output=str(self.root / 'model'))
        return argparse.Namespace(**(opts | values))

    def test_rejects_unsafe_reserved_and_existing_names(self):
        for name in ('../escape', 'bad-name', 'CON', 'nul', 'COM1', 'testGI', ''):
            with self.subTest(name=name), self.assertRaises(ValueError):
                create_game.create_game(name, False, False)
        self.assertFalse((self.root / 'projects').exists())

    def test_game_has_portable_and_visual_studio_entry_points(self):
        result = create_game.create_game('MyGame', False, False, directory=self.root / 'projects/MyGame')
        game = Path(result['directory'])
        self.assertTrue((game / 'CMakeLists.txt').exists())
        self.assertTrue((game / 'prog' / 'macosx_main.mm').exists())
        self.assertTrue((game / 'prog/editor.cpp').exists())
        self.assertTrue((game / 'prog/engine_paths.h').exists())
        self.assertIn(str(self.root).replace('\\', '/'), (game / 'CMakeLists.txt').read_text())
        self.assertIn('vulkan', (game / 'prog' / 'jamfile').read_text())
        self.assertIn('Metal', (game / 'prog' / 'jamfile').read_text())
        self.assertNotIn('@GAME_NAME@', (game / 'prog' / 'main.cpp').read_text())
        self.assertIn('Dagor Engine', Path(result['solution']).read_text(encoding='utf-8-sig'))
        ET.parse(result['project'])
        before = (game / 'prog' / 'main.cpp').read_bytes()
        with self.assertRaises(ValueError):
            create_game.create_game('MyGame', False, False)
        self.assertEqual(before, (game / 'prog' / 'main.cpp').read_bytes())

    def test_platform_and_architecture_reach_jam(self):
        for platform in ('windows', 'linux', 'macOS'):
            _, _, args = ide.invocation(self.options(platform=platform, arch='arm64'))
            self.assertIn('-sPlatform=' + platform, args)
            self.assertIn('-sPlatformArch=arm64', args)
        self.assertNotIn('ShaderCompiler2', ide.projects('linux'))

    def test_existing_project_registration_is_idempotent_and_rebases_jam_paths(self):
        create_game.create_game('MoveableGame', False, False, directory=self.root / 'projects/MoveableGame')
        registry = self.root / '_output/ide/project-registry.json'
        before = registry.read_bytes()
        ide.register_project(self.root / 'projects/MoveableGame')
        self.assertEqual(before, registry.read_bytes())
        _, _, args = ide.invocation(self.options(project='MoveableGame'))
        self.assertIn('-sRoot=' + self.root.as_posix(), args)
        self.assertIn('-sLocation=projects/MoveableGame/prog', args)

    def test_runtime_paths_follow_platform_layout(self):
        create_game.create_game('MyGame', False, False, directory=self.root / 'projects/MyGame')
        exe, cwd = ide.runtime(self.options(project='dargbox', platform='macOS', arch='arm64'))
        self.assertEqual(exe, self.root / 'tools/dargbox/dargbox-arm64.app/Contents/MacOS/dargbox-dev')
        self.assertEqual(cwd, self.root / 'tools/dargbox')
        exe, _ = ide.runtime(self.options(project='MyGame', platform='linux', config='rel'))
        self.assertEqual(exe, self.root / 'projects/MyGame/game/linux-x86_64/MyGame')

    def test_multiplayer_template_contains_real_host_client_transport(self):
        result = create_game.create_game('NetworkGame', False, False, directory=self.root / 'projects/NetworkGame', template_name='multiplayer')
        game = Path(result['directory'])
        self.assertTrue((game / 'prog/multiplayer.cpp').exists())
        self.assertTrue((game / 'prog/editor.cpp').exists())
        self.assertIn('3rdPartyLibs/enet', (game / 'prog/jamfile').read_text())
        self.assertIn('multiplayer::update()', (game / 'prog/main.cpp').read_text())

    def test_standard_compilation_database_has_source_and_output_arguments(self):
        folder = self.root / 'prog/tools/converters/dag2blk'
        folder.mkdir(parents=True)
        source = folder / 'main.cpp'
        source.write_text('int main() {}')
        entry = {'directory': str(folder), 'arguments': ['/bin/clang++', '-Iinclude', '-DTEST=1', ''],
                 'file': str(source), 'output': str(folder / 'main.o')}
        with patch.object(ide, 'commands_from_jam', return_value=[entry]):
            ide.generate(self.options(platform='linux'))
        database = json.loads((self.root / 'model/compile_commands.json').read_text())
        self.assertEqual(database[0]['arguments'][-3:], [str(source), '-o', str(folder / 'main.o')])
        self.assertIn('DAGOR_COMPILER', (self.root / 'model/dagor-model.cmake').read_text())


if __name__ == '__main__':
    unittest.main()
