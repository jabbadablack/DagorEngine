#!/usr/bin/env python3
"""While jam and CMake coexist: the jamfiles changed since <base> whose directory has a CMakeLists.txt that did not
change too, and the ported directories that still have TODO(jam) lines (deleted together with jam).

python check_sync.py [<base git revision, default origin/main>]  -- exit code 1 when either list is not empty
"""
import os
import subprocess
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))


def git(*args):
  return subprocess.run(['git', *args], cwd=ENGINE, capture_output=True, text=True, check=True).stdout.split('\n')


def main(argv):
  base = argv[0] if argv else 'origin/main'
  changed = {p for p in git('diff', '--name-only', base + '...HEAD') + git('diff', '--name-only', 'HEAD') if p}
  problems = []
  for path in sorted(changed):
    d, name = os.path.split(path)
    if (name == 'jamfile' or name.startswith('jamfile-') or name.endswith('.jam')) and not path.startswith('prog/_jBuild'):
      lists = d + '/CMakeLists.txt'
      if os.path.exists(os.path.join(ENGINE, lists)) and lists not in changed:
        problems.append('{} changed, {} did not'.format(path, lists))
  for line in git('grep', '-n', 'TODO(jam)', '--', '*CMakeLists.txt', '*.cmake'):
    if line:
      problems.append('unported: ' + line)
  for p in problems:
    print(p)
  return 1 if problems else 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
