#!/usr/bin/env python3
# creates a game project from a template in templates/, see `python new_project.py --help`
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), 'prog', 'tools'))
from pythonCommon.dagorProject import create  # noqa: E402

if __name__ == '__main__':
  sys.exit(create.main(sys.argv[1:]))
