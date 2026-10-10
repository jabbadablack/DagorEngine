#!/usr/bin/env python3
"""Dagor Engine commands: python dng.py <command> [arguments], python dng.py <command> -h for its arguments.

  devtools  downloads and sets up the build toolkit (compilers, SDKs, jam)
  build     builds the engine tools, dargbox, the project template and, when named, the samples
  new       creates a game project from a template in templates/
  test      builds and runs the engine and project tests
"""
import os
import sys

if sys.version_info < (3, 8):
  sys.exit('dng.py needs Python 3.8 or newer')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'prog', 'tools'))


def devtools(argv):
  from pythonCommon import dagorDevtools
  return dagorDevtools.main(argv)


def build(argv):
  from pythonCommon.dagorBuild import cli
  return cli.main(argv)


def new(argv):
  from pythonCommon.dagorProject import create
  return create.main(argv)


def test(argv):
  from pythonCommon.dagorBuild import ENGINE_ROOT, HOST, HOST_ARCH, TOOLS_DIR
  from pythonCommon.dagorTest import cli
  return cli.main(argv, ENGINE_ROOT, HOST, HOST_ARCH, TOOLS_DIR)


COMMANDS = {'devtools': devtools, 'build': build, 'new': new, 'test': test}

if __name__ == '__main__':
  if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
    print(__doc__.strip())
    sys.exit(0 if sys.argv[1:2] in (['-h'], ['--help']) else 2)
  sys.exit(COMMANDS[sys.argv[1]](sys.argv[2:]))
