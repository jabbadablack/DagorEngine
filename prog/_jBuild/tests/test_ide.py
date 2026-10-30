import argparse
import contextlib
import importlib.util
import io
import json
import os
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
        for _, relative in generate_projects.PROJECTS:
            placeholder = self.root / relative
            placeholder.parent.mkdir(parents=True, exist_ok=True)
            placeholder.write_text('<Project/>')
        shared = self.root / 'prog' / 'prog.vcxproj'
        shared.parent.mkdir(parents=True, exist_ok=True)
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
        self.assertTrue((game / 'prog/scripts/game/main.das').exists())
        self.assertTrue((game / 'prog/scripts/ui/main.nut').exists())
        self.assertTrue((game / 'develop/assets/primitives/cube.lod00.dag').exists())
        self.assertTrue((game / 'develop/gui/fonts/OFL.txt').exists())
        self.assertFalse(list((game / 'game').rglob('*.das')))
        self.assertFalse((game / 'prog/editor.cpp').exists())
        self.assertIn(str(self.root).replace('\\', '/'), (game / 'CMakeLists.txt').read_text())
        self.assertIn('daNetGame/setup.jam', (game / 'prog/jamfile').read_text())
        self.assertIn('%daeditor/editor.nut', (game / 'prog/scripts/ui/main.nut').read_text())
        for file in game.rglob('*'):
            if file.is_file() and file.suffix in ('.py', '.blk', '.das', '.nut', '.json', '.jam', '.md'):
                text = file.read_text(encoding='utf-8')
                self.assertNotIn('outerSpace', text, str(file))
                self.assertNotIn('outer_space', text, str(file))
                self.assertNotIn('testGI', text, str(file))
        self.assertIn('MyGame.vcxproj', Path(result['solution']).read_text(encoding='utf-8-sig'))
        self.assertNotIn('Dagor Engine', Path(result['solution']).read_text(encoding='utf-8-sig'))
        self.assertTrue((game / 'prog/build.py').exists())
        self.assertEqual({p.stem.lower() for p in (game / 'develop').glob('*.cmd')}, {'dabuild', 'daviewer', 'daeditor'})
        self.assertFalse(list(game.glob('*.cmd')))
        self.assertFalse(list(game.glob('*.sh')))
        self.assertNotIn('dng.py', (game / 'develop/dabuild.cmd').read_text())
        self.assertIn('entName:t="cube"', (game / 'develop/levels/starter/heightmapLand/entities.blk').read_text())
        self.assertIn('content/mygame/levels/starter.bin', (game / 'prog/gameBase/gamedata/levels/starter.blk').read_text())
        self.assertTrue((game / 'CMakePresets.json').exists())
        ET.parse(result['project'])
        before = (game / 'prog/scripts/game/main.das').read_bytes()
        with self.assertRaises(ValueError):
            create_game.create_game('MyGame', False, False)
        self.assertEqual(before, (game / 'prog/scripts/game/main.das').read_bytes())

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
        self.assertNotIn('-sLocation=projects/MoveableGame/prog', args)
        self.assertIn('Location ?= "projects/MoveableGame/prog"', (self.root / 'projects/MoveableGame/prog/jamfile').read_text())

    def test_runtime_paths_follow_platform_layout(self):
        create_game.create_game('MyGame', False, False, directory=self.root / 'projects/MyGame')
        exe, cwd = ide.runtime(self.options(project='dargbox', platform='macOS', arch='arm64'))
        self.assertEqual(exe, self.root / 'tools/dargbox/dargbox-arm64.app/Contents/MacOS/dargbox-dev')
        self.assertEqual(cwd, self.root / 'tools/dargbox')
        exe, _ = ide.runtime(self.options(project='MyGame', platform='linux', config='rel'))
        self.assertEqual(exe, self.root / 'projects/MyGame/game/linux-x86_64/MyGame')

    def test_moving_game_to_another_engine_rebases_content_and_build_paths(self):
        result = create_game.create_game('MoveableGame', False, False, directory=self.root / 'projects/MoveableGame')
        game = Path(result['directory'])
        new_engine = self.root / 'another engine'
        source = game / 'prog/scripts/game/main.das'
        before = source.read_bytes()
        with patch.object(ide, 'ROOT', new_engine):
            ide.register_project(game)
        manifest = json.loads((game / 'dng-project.json').read_text())
        self.assertEqual(manifest['engine'], str(new_engine))
        settings = (game / 'prog/gameBase/config/settings.blk').read_text()
        self.assertIn(new_engine.as_posix() + '/prog/scripts/sq/daRg', settings)
        self.assertNotIn(self.root.as_posix() + '/prog/scripts/sq/daRg', settings)
        self.assertIn(manifest['engine_from_prog'] + '/prog/gameLibs', (game / 'prog/mk.vromfs.blk').read_text())
        self.assertEqual(source.read_bytes(), before)

    def test_multiplayer_template_contains_real_host_client_transport(self):
        result = create_game.create_game('NetworkGame', False, False, directory=self.root / 'projects/NetworkGame', template_name='multiplayer')
        game = Path(result['directory'])
        self.assertTrue((game / 'develop/daEditor.cmd').exists())
        self.assertTrue((game / 'prog/scripts/ui/main.nut').exists())
        self.assertIn('daNetGame', (game / 'prog/jamfile').read_text())

    def test_ui_editor_quotes_script_path_for_inline_config_parser(self):
        import game_project
        from unittest.mock import Mock
        game = self.root / 'game with spaces'
        run = Mock()
        opts = argparse.Namespace(directory=str(game), action='ui-editor', dry_run=True)
        with patch.object(ide, 'runtime', return_value=(Path('dargbox'), self.root)):
            game_project.launch_tool(opts, [], run)
        self.assertEqual(run.call_args.args[0][1], '-config:script:t=' + json.dumps((game / 'prog/scripts/ui/main.nut').as_posix()))

    def test_game_local_launcher_forwards_runtime_arguments_after_separator(self):
        result = create_game.create_game('LaunchGame', False, False, directory=self.root / 'projects/game with spaces')
        game = Path(result['directory'])
        helper = self.root / 'prog/_jBuild/ide.py'
        helper.parent.mkdir(parents=True, exist_ok=True)
        helper.touch()
        spec = importlib.util.spec_from_file_location('game_local_build', game / 'prog/build.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        output = io.StringIO()
        with patch.object(sys, 'argv', ['build.py', '--no-build', '--run', '--dry-run', '--', '--connect:127.0.0.1:20000']), \
             patch.object(sys, 'path', list(sys.path)), patch.dict(os.environ), contextlib.redirect_stdout(output):
            self.assertEqual(build.main(), 0)
        self.assertIn('--connect:127.0.0.1:20000', output.getvalue())
        self.assertIn('LaunchGame-dev.exe' if ide.host_platform() == 'windows' else 'LaunchGame-dev', output.getvalue())

    def test_standard_compilation_database_has_source_and_output_arguments(self):
        folder = self.root / 'prog/tools/converters/dag2blk'
        folder.mkdir(parents=True, exist_ok=True)
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
