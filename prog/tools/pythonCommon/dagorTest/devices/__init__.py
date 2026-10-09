"""Device backend registry; see base.py for the backend interface."""
import importlib.util
import inspect
import os

from .base import DeviceBackend
from .local import LocalDevice

BUILTIN_BACKENDS = [LocalDevice]


def _load_plugin_backends():
  backends = []
  for d in filter(None, os.environ.get('DAGOR_TEST_DEVICE_PATH', '').split(os.pathsep)):
    if not os.path.isdir(d):
      raise RuntimeError('DAGOR_TEST_DEVICE_PATH entry {} is not a directory'.format(d))
    for fn in sorted(os.listdir(d)):
      if not fn.endswith('.py') or fn.startswith('_'):
        continue
      spec = importlib.util.spec_from_file_location('dagor_test_device_' + fn[:-3], os.path.join(d, fn))
      module = importlib.util.module_from_spec(spec)
      spec.loader.exec_module(module)
      backends += [c for _, c in inspect.getmembers(module, inspect.isclass) if issubclass(c, DeviceBackend) and c.name]
  return backends


def backend_classes():
  classes = {}
  for c in BUILTIN_BACKENDS + _load_plugin_backends():
    if c.name in classes and classes[c.name] is not c:
      raise RuntimeError('two device backends are named {!r}'.format(c.name))
    classes[c.name] = c
  return classes


def create(spec: str) -> DeviceBackend:
  """spec is <backend>[:<device id>], e.g. local, android:emulator-5554."""
  name, _, device_id = spec.partition(':')
  classes = backend_classes()
  if name not in classes:
    raise RuntimeError('unknown device backend {!r}, available: {}'.format(name, ', '.join(sorted(classes))))
  return classes[name](device_id or None)
