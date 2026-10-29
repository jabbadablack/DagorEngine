"""Pure Python regression tests for typed object-property scripts."""
import importlib.util
from pathlib import Path

path = Path(__file__).resolve().parents[1] / 'object_properties/codec.py'
spec = importlib.util.spec_from_file_location('dagor_property_codec', path)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)

values = {
    'label:t': 'Case Sensitive = One; Two "Quoted" ~ Tilde\nNew Line',
    'path:t': r'C:\Art Assets\MiXeD\Texture.dds',
    'url:t': 'https://example.test/a=b',
    'empty:t': '',
    'enabled:b': False,
    'count:i': 12,
    'roughness:r': 0.25,
    'offset:p3': [1.0, -2.0, 3.5],
    'size:ip2': [10, 20],
    'matrix:m': [1.0, 0, 0, 0, 1.0, 0, 0, 0, 1.0, 2, 3, 4],
}
encoded = codec.serialize_properties(values)
assert codec.parse_properties(encoded) == values
parsed = codec.parse_properties('first:i=1; second:b=no // comment\nlabel:t="Hello World = a;b"')
assert parsed == {'first:i': 1, 'second:b': False, 'label:t': 'Hello World = a;b'}
parsed = codec.parse_properties('bad:i=3.5; vector:p3=1,2; valid:t="Still Here"')
assert parsed['valid:t'] == 'Still Here'
assert 'bad:i=3.5' in parsed['broken_properties:t']
assert 'vector:p3=1,2' in parsed['broken_properties:t']
assert codec.parse_properties(codec.serialize_properties(parsed)) == parsed
assert not codec.as_bool('FALSE') and not codec.as_bool('no')
assert codec.as_bool('YES')
print('PASS: typed property roundtrip, case/spaces, equals/semicolons, tilde escapes, matrices, malformed-data retention')
