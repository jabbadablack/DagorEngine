#!/usr/bin/env python3
"""Dagor Engine commands: python dng.py <command> [arguments], python dng.py <command> -h for its arguments.

  build     builds the engine tools, dargbox, the project template and, when named, the samples
"""
import os
import sys

if sys.version_info < (3, 8):
  sys.exit('dng.py needs Python 3.8 or newer')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prog', 'tools'))


def build(argv):
  from pythonCommon.dagorBuild import cli
  return cli.main(argv)


COMMANDS = {'build': build}

if __name__ == '__main__':
  if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
    print(__doc__.strip())
    sys.exit(0 if sys.argv[1:2] in (['-h'], ['--help']) else 2)
  sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]))
