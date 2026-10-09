#!/usr/bin/env python3
"""Commands of this project: python project.py {setup,relink,build,test,info} (-h for help).

The engine checkout is named by engine.blk; the commands themselves live in the engine
(prog/tools/pythonCommon/dagorProject), so they follow the engine version the project is built with.
"""
import os
import re
import sys

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
CODENAME = 'dng_empty'  # base name of the executables (dng_empty-dev, dng_empty-ded-dev) and of the main vromfs


def engine_root():
  """The engine checkout named by engine.blk: engineRoot:t="<path relative to this dir, or absolute>"."""
  fn = os.path.join(PROJECT_DIR, 'engine.blk')
  with open(fn, 'r', encoding='utf-8') as f:
    m = re.search(r'^\s*engineRoot\s*:\s*t\s*=\s*"([^"]*)"', f.read(), re.MULTILINE)
  if not m:
    sys.exit('{}: expected engineRoot:t="<path to the engine checkout>"'.format(fn))
  root = os.path.normpath(os.path.join(PROJECT_DIR, re.sub(r'~(.)', r'\1', m.group(1))))  # ~ escapes in BLK strings
  if not os.path.isdir(os.path.join(root, 'prog', 'tools', 'pythonCommon', 'dagorProject')):
    sys.exit('{}: "{}" is not a Dagor Engine checkout with project support; set engineRoot to the engine dir'.format(fn, root))
  return root


def load():
  """The engine's dagorProject package and this project."""
  sys.path.insert(0, os.path.join(engine_root(), 'prog', 'tools'))
  from pythonCommon import dagorProject
  return dagorProject, dagorProject.Project(PROJECT_DIR, CODENAME)


if __name__ == '__main__':
  dagorProject, project = load()
  from pythonCommon.dagorProject import cli
  sys.exit(cli.main(project, sys.argv[1:]))
