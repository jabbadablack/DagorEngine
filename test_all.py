#!/usr/bin/env python3
# builds and runs DagorEngine and game project tests, see `python test_all.py --help`
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'prog', 'tools'))
from pythonCommon.dagorBuild import ENGINE_ROOT, HOST, HOST_ARCH, TOOLS_DIR  # noqa: E402
from pythonCommon.dagorTest import cli  # noqa: E402

if __name__ == '__main__':
  sys.exit(cli.main(sys.argv[1:], ENGINE_ROOT, HOST, HOST_ARCH, TOOLS_DIR))
