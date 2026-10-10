#!/usr/bin/env python3
"""Inventory of what jam builds, for the port to CMake (deleted together with jam).

For each root of roots.txt, plus every unit test of a test.blk manifest, it runs jam as a dry run (jam -n -a -dx) and
reads from the dump each target jam would build: its output dir (the global settings, like ~krnlimp or ~ex), its
sources with their full compile commands, and the libraries a program links. Results:

  inventory.json      every target of every root (input of parity.py)
  variant_matrix.md   source dirs that jam builds as more than one library, or with different flags, among the roots of
                      one CMake tree: each needs a tree option, a selector library or a decision in decisions.md

python inventory.py [--platform windows] [--arch x86_64] [--config dev] [--tree <tree>...] [--out <dir>]
"""
import argparse
import collections
import concurrent.futures
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
HERE = os.path.dirname(os.path.abspath(__file__))

DIGEST = re.compile(r'^\s*echo digest_(\w+) = (.*?) ; >>(\S+)\.digest\s*$')
COMPILE = re.compile(r'^\s*call_filtered (\S+) (.*?)#\\\((.*)\)\\#\s*$')
OUTPUT_DIR = re.compile(r'_output/([^/]+)/_(.+?\.(?:lib|a|exe|dll|so|dylib))(?:/|$)')  # objects of subdirs too
COMPILERS = {'cl', 'clang-cl', 'clang', 'clang++', 'gcc', 'g++', 'lcc', 'l++'}


def roots(trees):
  """(tree, cwd, jam args) of roots.txt and of the unit test manifests."""
  result = []
  with open(os.path.join(HERE, 'roots.txt')) as f:
    for line in f:
      line = line.split('#', 1)[0].strip()
      if line:
        tree, cwd, *args = shlex.split(line)
        result.append((tree, cwd, args))
  for dirpath, dirnames, filenames in os.walk(os.path.join(ENGINE, 'prog')):
    dirnames[:] = [d for d in dirnames if d not in ('_output', '3rdPartyLibs', '.git', '__pycache__')]
    if 'test.blk' in filenames:
      with open(os.path.join(dirpath, 'test.blk'), encoding='utf-8', errors='replace') as f:
        for jamfile in re.findall(r'jamfile:t="([^"]+)"', f.read()):
          cwd = os.path.relpath(dirpath, ENGINE).replace(os.sep, '/')
          args = [] if jamfile == 'jamfile' else ['-f' + jamfile]
          result.append(('tests', cwd, args))
  return [r for r in result if not trees or r[0] in trees]


def tool(path):
  name = os.path.basename(path).lower()
  return re.sub(r'(-\d+)?(\.exe)?$', '', name)


def run_root(root, jam, common):
  tree, cwd, args = root
  cmd = [jam, '-n', '-a', '-dx'] + common + args
  proc = subprocess.run(cmd, cwd=os.path.join(ENGINE, cwd), capture_output=True, text=True, errors='replace')
  return root, cmd, proc.returncode, proc.stdout + proc.stderr


INCLUDE_FLAGS = ('-I', '/I', '-imsvc', '-isystem')


def engine_relative(args, cwd):
  """The compiler arguments with relative include dirs relative to the engine root instead of to the root's dir: one
  library's command is kept for every root that builds it."""
  result = []
  it = iter(args)
  for a in it:
    flag = next((f for f in INCLUDE_FLAGS if a.startswith(f)), None)
    if flag is None:
      result.append(a)
      continue
    d = a[len(flag):]
    if d:
      prefix = flag
    else:  # the dir is the next argument
      result.append(a)
      d, prefix = next(it, ''), ''
    if d and not os.path.isabs(d):
      d = os.path.relpath(os.path.normpath(os.path.join(ENGINE, cwd, d)), ENGINE).replace(os.sep, '/')
    result.append(prefix + d)
  return result


def parse(dump, cwd):
  """{<output dir>/<target>: target} of one dump."""
  targets = {}

  def target(out_path):
    # not normalized: jam places the objects of a library's ../ sources under its dir with the ../ kept
    path = os.path.join(ENGINE, cwd, out_path).replace(os.sep, '/')
    m = OUTPUT_DIR.search(path)
    if not m:
      return None
    cfg, name = m.group(1), m.group(2)
    key = cfg + '/' + name
    return targets.setdefault(key, {'output': cfg, 'name': name, 'sources': {}, 'digest': {}})

  for line in dump.splitlines():
    m = DIGEST.match(line)
    if m:
      t = target(os.path.dirname(m.group(3)))
      if t is not None:
        t['digest'][m.group(1)] = m.group(2).split()
      continue
    m = COMPILE.match(line)
    if m and tool(m.group(1)) in COMPILERS:
      inner = m.group(3).split()
      obj, src = None, None
      it = iter(inner)
      rest = []
      for tok in it:
        if tok.startswith('-Fo'):
          obj = tok[3:]
        elif tok == '-o':
          obj = next(it, None)
        else:
          rest.append(tok)
      if obj and rest:
        src = os.path.normpath(os.path.join(ENGINE, cwd, rest[-1])).replace(os.sep, '/')
        t = target(os.path.dirname(obj))
        if t is not None:
          t['sources'][os.path.relpath(src, ENGINE).replace(os.sep, '/')] = engine_relative(m.group(2).split(), cwd)
  return targets


def kind(name):
  ext = os.path.splitext(name)[1].lower()
  return {'.lib': 'lib', '.a': 'lib', '.exe': 'exe', '.dll': 'dll', '.so': 'dll', '.dylib': 'dll'}.get(ext, 'exe')


def source_dir(t):
  dirs = sorted({os.path.dirname(s) for s in t['sources']})
  if not dirs:
    return None
  common = os.path.commonpath(dirs).replace(os.sep, '/')
  return common


def flags_digest(t):
  opts = ' '.join(t['digest'].get('optCpp', []) + t['digest'].get('optC', []))
  return hashlib.sha1(opts.encode()).hexdigest()[:8]


def matrix(inventory):
  """Markdown of the source dirs built in more than one way within one tree."""
  per_tree = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(set)))
  for root in inventory['roots']:
    for key in root['targets']:
      t = inventory['targets'][key]
      if kind(t['name']) != 'lib':
        continue
      d = source_dir(t)
      if d:
        variant = '{} [{} flags {}]'.format(os.path.basename(t['name']), t['output'], flags_digest(t))
        per_tree[root['tree']][d][variant].add(root['id'])
  outputs = collections.defaultdict(lambda: collections.defaultdict(list))
  for root in inventory['roots']:
    for key in root['targets']:
      t = inventory['targets'][key]
      if kind(t['name']) != 'lib':
        outputs[root['tree']][t['output']].append(os.path.basename(t['name']))
  lines = ['# Variant matrix', '',
           'Libraries jam builds in more than one way among the roots of one CMake tree (generated by inventory.py).',
           'Each variant is `<lib name> [<jam output dir> flags <hash of its compile options>]` with the roots using it.',
           '']
  lines += ['## Programs by jam output dir (global settings)', '']
  for tree in sorted(outputs):
    lines.append('- tree `{}`'.format(tree))
    for out in sorted(outputs[tree]):
      lines.append('  - `{}`: {}'.format(out, ', '.join(sorted(set(outputs[tree][out])))))
  lines.append('')
  for tree in sorted(per_tree):
    dirs = {d: v for d, v in per_tree[tree].items() if len(v) > 1}
    lines += ['## Tree `{}`: {} of {} library dirs vary'.format(tree, len(dirs), len(per_tree[tree])), '']
    for d in sorted(dirs):
      lines.append('- `{}`'.format(d))
      for variant in sorted(dirs[d]):
        users = sorted(dirs[d][variant])
        shown = ', '.join(users[:4]) + (' (+{} more)'.format(len(users) - 4) if len(users) > 4 else '')
        lines.append('  - {}: {}'.format(variant, shown))
    lines.append('')
  return '\n'.join(lines)


def main(argv):
  parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
  parser.add_argument('--platform', default={'win32': 'windows', 'darwin': 'macOS'}.get(sys.platform, 'linux'))
  parser.add_argument('--arch', default='x86_64')
  parser.add_argument('--config', default='dev')
  parser.add_argument('--tree', action='append', default=[])
  parser.add_argument('--out', default=os.path.join(ENGINE, '_output', 'jam2cmake'))
  parser.add_argument('-j', type=int, default=os.cpu_count())
  args = parser.parse_args(argv)

  jam = shutil.which('jam')
  if not jam:
    sys.exit('jam is not on PATH')
  common = ['-sPlatform=' + args.platform, '-sPlatformArch=' + args.arch, '-sConfig=' + args.config]
  inventory = {'platform': args.platform, 'arch': args.arch, 'config': args.config, 'roots': [], 'targets': {}}
  failed = []
  with concurrent.futures.ThreadPoolExecutor(args.j) as pool:
    for (tree, cwd, jam_args), cmd, code, dump in pool.map(lambda r: run_root(r, jam, common), roots(args.tree)):
      root_id = ' '.join([cwd] + [a for a in jam_args if not a.startswith('-sRoot=')])
      targets = parse(dump, cwd)
      if code != 0 or not targets:
        failed.append('{} (exit {}): {}'.format(root_id, code, dump.strip().splitlines()[-1:] if dump.strip() else ''))
        continue
      inventory['roots'].append({'id': root_id, 'tree': tree, 'cwd': cwd, 'args': jam_args, 'targets': sorted(targets)})
      for key, t in targets.items():
        known = inventory['targets'].setdefault(key, t)
        known['sources'].update(t['sources'])
        known['digest'].update(t['digest'])

  os.makedirs(args.out, exist_ok=True)
  with open(os.path.join(args.out, 'inventory.json'), 'w') as f:
    json.dump(inventory, f, indent=1, sort_keys=True)
  with open(os.path.join(args.out, 'variant_matrix.md'), 'w') as f:
    f.write(matrix(inventory) + '\n')
  print('{} roots, {} targets -> {}'.format(len(inventory['roots']), len(inventory['targets']), args.out))
  for line in failed:
    print('FAILED ' + line, file=sys.stderr)
  return 1 if failed else 0


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
