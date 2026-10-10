#!/usr/bin/env python3
"""Compares what a CMake tree compiles with what jam compiles for the same roots (deleted together with jam).

For each jam target of the chosen roots (from inventory.json; of a target jam built in several variants there, the
closest variant), it finds the CMake compiles of the same source files in the tree's compile_commands.json and reports:
  - sources jam compiles that the CMake tree does not (and, per matched target dir, the other way round)
  - preprocessor definitions and include dirs that differ for a source
Include dirs that do not exist are not compared (jam passed several). Compiler-specific flags are not compared: the
trees may use another compiler than jam did for that root. Intended differences go into parity_allowlist.txt, one regex
per line matched against the report line, with the reason after it.

python parity.py <build dir> [--config Dev] [--root <substring of a root id>...] [--inventory <inventory.json>]
"""
import argparse
import collections
import json
import os
import re
import shlex
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))
# the toolchain's own include dirs, which jam and CMake spell differently
SYSTEM_DIRS = re.compile(r'(devtools|/dagor/sdk/|windows kits|microsoft visual studio|/llvm|/usr/include|xcode)',
                         re.IGNORECASE)
# definitions of the toolchain or of the build system itself
IGNORED_DEFINES = re.compile(r'^(CMAKE_INTDIR|_TARGET_SIMD_SSE|_SECURE_SCL|WIN32)$')


def norm_path(path, base):
  p = os.path.normpath(os.path.join(base, path.strip('"')))
  return os.path.normcase(p).replace(os.sep, '/')


def rel(path):
  return os.path.relpath(path, ENGINE).replace(os.sep, '/')


def split(cmd):
  return shlex.split(cmd, posix=not sys.platform.startswith('win')) if isinstance(cmd, str) else cmd


def flags(args, base):
  """(definitions, include dirs) of a compiler command line, of either MSVC or GNU style."""
  defines, includes = set(), set()
  it = iter(args)
  for a in it:
    a = a.strip('"')
    for prefix in ('-D', '/D'):
      if a.startswith(prefix):
        d = a[2:] or next(it, '')
        name = d.split('=', 1)[0]
        if not IGNORED_DEFINES.match(name):
          defines.add(d.replace('\\"', '"').replace('""', ''))
        break
    else:
      for prefix in ('-I', '/I', '-imsvc', '-isystem'):
        if a.startswith(prefix):
          d = a[len(prefix):] or next(it, '')
          path = norm_path(d, base)
          if not SYSTEM_DIRS.search(path) and (os.path.isdir(path) or path.startswith(GENERATED)):
            includes.add(path)
          break
  return defines, includes


# include dirs of generated files, which exist only once the tree is built
GENERATED = os.path.normcase(os.path.join(ENGINE, 'build')).replace(os.sep, '/') + '/'
# sources the inventory has no commands for: jam's dry run lists compilers only, not assemblers
ASSEMBLY = ('.asm', '.masm', '.nasm', '.nas', '.s')
TARGET_DIR = re.compile(r'CMakeFiles[\\/]([^\\/]+)\.dir[\\/]')


def cmake_compiles(build_dir, config):
  """{normalized source path: [(target, defines, includes)]} of the tree's compile_commands.json for one configuration;
  a source of several targets (flavors) has an entry for each."""
  with open(os.path.join(build_dir, 'compile_commands.json')) as f:
    entries = json.load(f)
  marker = '/{}/'.format(config).lower()

  def output(e):
    return '/' + e.get('output', '').replace('\\', '/').lower()

  multi_config = any(marker in output(e) for e in entries)  # Ninja Multi-Config lists every configuration
  result = collections.defaultdict(list)
  for e in entries:
    if multi_config and marker not in output(e):
      continue
    args = e['arguments'] if 'arguments' in e else split(e['command'])
    m = TARGET_DIR.search(e.get('output', ''))
    target = m.group(1) if m else '?'
    result[norm_path(e['file'], e['directory'])].append((target,) + flags(args, e['directory']))
  return result


def load_allowlist(build_dir):
  """The allowlist's rules for this tree: a rule starting with '@<regex> ' applies only to trees whose build dir name
  matches the regex (@tests: the tests trees)."""
  path = os.path.join(HERE, 'parity_allowlist.txt')
  tree = os.path.basename(os.path.normpath(build_dir))
  rules = []
  if os.path.exists(path):
    with open(path) as f:
      for line in f:
        line = line.split('  #', 1)[0].strip()
        if not line or line.startswith('#'):
          continue
        if line.startswith('@'):
          scope, line = line[1:].split(None, 1)
          if not re.search(scope, tree):
            continue
        rules.append(re.compile(line))
  return rules


def compare(t, cmake):
  """(report lines, sources compared, the CMake target compiling most of them) of one jam target."""
  report = []
  compared = 0
  # the CMake target of the same name (engine/perfMon/stub.lib -> engine.perfMon.stub) when it compiles the source
  own = os.path.splitext(t['name'])[0].replace('/', '.')
  cmake_targets = collections.Counter()
  for src, cmd in sorted(t['sources'].items()):
    path = norm_path(src, ENGINE)
    if path not in cmake:
      report.append('{}: {}: not compiled by CMake'.format(t['name'], src))
      continue
    compared += 1
    jd, ji = flags(cmd, ENGINE)  # inventory.py made the include dirs relative to the engine root
    # the CMake compile of this source in the target of the same name, else the one closest to jam's (a source of
    # several targets or flavors is compiled several times)
    target, cd, ci = min(cmake[path], key=lambda c: (c[0] != own, len(jd ^ c[1]) + len(ji ^ c[2])))
    cmake_targets[target] += 1
    for d in sorted(jd - cd):
      report.append('{}: {}: define only in jam: {}'.format(t['name'], src, d))
    for d in sorted(cd - jd):
      report.append('{}: {}: define only in CMake: {}'.format(t['name'], src, d))
    for i in sorted(ji - ci):
      report.append('{}: {}: include only in jam: {}'.format(t['name'], src, rel(i)))
    for i in sorted(ci - ji):
      report.append('{}: {}: include only in CMake: {}'.format(t['name'], src, rel(i)))
  return report, compared, cmake_targets.most_common(1)[0][0] if cmake_targets else None


def main(argv):
  parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
  parser.add_argument('build_dir')
  parser.add_argument('--config', default='Dev')
  parser.add_argument('--root', action='append', default=[], help='substring of the root ids to compare')
  parser.add_argument('--inventory', default=os.path.join(ENGINE, '_output', 'jam2cmake', 'inventory.json'))
  args = parser.parse_args(argv)

  with open(args.inventory) as f:
    inventory = json.load(f)
  cmake = cmake_compiles(args.build_dir, args.config)
  allow = load_allowlist(args.build_dir)

  # the jam variants of each target the roots build (a library can be built with and without exceptions, say)
  variants = collections.defaultdict(list)
  for root in inventory['roots']:
    if args.root and not any(r in root['id'] for r in args.root):
      continue
    for key in root['targets']:
      t = inventory['targets'][key]
      if key not in variants[t['name']]:
        variants[t['name']].append(key)

  report = []
  compared = 0
  seen = set()
  for name, keys in sorted(variants.items()):
    # a CMake tree builds a target one way: it is compared with the closest of jam's variants
    best = min((compare(inventory['targets'][k], cmake) + (k,) for k in keys),
               key=lambda r: sum(1 for line in r[0] if not any(a.search(line) for a in allow)))
    lines, count, target, key = best
    report += lines
    compared += count
    # sources that CMake target compiles and jam's did not
    jam_sources = {norm_path(s, ENGINE) for s in inventory['targets'][key]['sources']}
    for path, compiles in sorted(cmake.items()):
      if (path not in jam_sources and path not in seen and not path.endswith(ASSEMBLY)
          and any(c[0] == target for c in compiles)):
        seen.add(path)
        report.append('{}: {}: compiled only by CMake'.format(name, rel(path)))

  shown = [line for line in report if not any(r.search(line) for r in allow)]
  for line in shown:
    print(line)
  print('{} sources compared, {} differences ({} allowed)'.format(compared, len(shown), len(report) - len(shown)),
        file=sys.stderr)
  return 1 if shown else 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
