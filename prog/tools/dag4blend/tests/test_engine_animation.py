"""Compile Blender-produced A2D through the repository's real daBuild plugin."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import sys
import types

from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[2]
TOOLS = REPOSITORY / 'tools/dagor_cdk/windows-x86_64'
package = types.ModuleType('dagor_engine_fixture')
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
spec = importlib.util.spec_from_file_location(package.__name__ + '.animation', ROOT / 'animation.py')
animation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(animation)
assert (TOOLS / 'daBuild-dev.exe').is_file(), 'Engine validator requires the Windows CDK'
with tempfile.TemporaryDirectory(prefix='dagor-engine-animation-', dir=ROOT / 'tests') as folder:
    folder = Path(folder)
    assert folder.resolve().is_relative_to(ROOT / 'tests')
    assets = folder / 'assets'
    assets.mkdir()
    tracks = {'root': ([Vector((0, 0, 0)), Vector((1, 2, 3)), Vector((2, 4, 6))],
                       [Quaternion(), Quaternion((0, 1, 0), 0.5), Quaternion((0, 1, 0), 1)],
                       [Vector((1, 1, 1))] * 3)}
    velocities = animation.origin_velocities([Matrix.Translation((index, 0, 0)) for index in range(3)], [0, 200, 400])
    (assets / 'clip.a2d').write_bytes(animation.encode_a2d(tracks, [0, 200, 400],
        [('start', 0), ('end', 400)], {animation.POSITION: 1e-4, animation.SCALE: 1e-4,
                                     animation.ROTATION: 1e-4}, velocities))
    (assets / 'clip.a2d.blk').write_text('name:t="clip.a2d"\n', encoding='utf8')
    plugin = (TOOLS / 'plugins/dabuild/a2dExp-dev.dll').as_posix()
    application = folder / 'application.blk'
    application.write_text('''assets {
  base:t="assets"
  types { type:t="a2d" }
  export {
    types { type:t="a2d" }
    plugins { plugin:t="''' + plugin + '''" }
    cache:t="cache"
    assetCache:t="asset-cache"
    destination { PC:t="res" }
  }
}
''', encoding='utf8')
    command = [str(TOOLS / 'daBuild-dev.exe'), '-target:PC', '-nopbar',
               '-build:clip:compiled.bin', str(application)]
    result = subprocess.run(command, cwd=folder, capture_output=True, text=True,
                            timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    assert result.returncode == 0, f'daBuild failed: {result.returncode}'
    output = folder / 'compiled.bin'
    assert output.is_file() and output.stat().st_size > 0, 'daBuild did not emit a compiled animation'
print('PASS: generated Anim-v2 source compiled by the real Dagor A2D asset exporter')
