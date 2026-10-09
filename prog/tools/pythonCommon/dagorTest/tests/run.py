#!/usr/bin/env python3
"""Self-tests of the test runner, registered in test.blk next to this file:

  python run.py --engine <root> --host windows --host-arch x86_64 --platform windows --arch x86_64 --config dev
"""
import argparse
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..')))  # prog/tools: pythonCommon is importable

if __name__ == '__main__':
  p = argparse.ArgumentParser()
  p.add_argument('--engine')
  for name in ('host', 'host-arch', 'platform', 'arch', 'config'):
    p.add_argument('--' + name)
  args = p.parse_args()
  if args.engine:
    for name in ('engine', 'host', 'host_arch', 'platform', 'arch', 'config'):
      os.environ['DAGORTEST_' + name.upper()] = getattr(args, name)
  suite = unittest.defaultTestLoader.discover(HERE, pattern='test_*.py', top_level_dir=HERE)
  ok = unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
  sys.exit(0 if ok else 1)
