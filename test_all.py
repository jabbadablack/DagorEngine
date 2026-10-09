#!/usr/bin/env python3
# builds and runs DagorEngine and game project tests, see `python test_all.py --help`
import os
import sys

from build_all import DAGOR_HOST, DAGOR_HOST_ARCH, DAGOR_ROOT_FOLDER, DAGOR_TOOLS_FOLDER

sys.path.insert(0, os.path.join(DAGOR_ROOT_FOLDER, 'prog', 'tools'))
from pythonCommon.dagorTest import cli  # noqa: E402

if __name__ == '__main__':
  sys.exit(cli.main(sys.argv[1:], DAGOR_ROOT_FOLDER, DAGOR_HOST, DAGOR_HOST_ARCH, DAGOR_TOOLS_FOLDER))
