"""Keeps Gaijin hosts out of the fork: finds gaijin.net, gaijinent.com and gaijin.lan outside comments in the shipping code,
the tools and the build scripts, and upstream GitHub release URLs in the build scripts.

python host_guard.py [engine_root]  -- prints path:line: host for each finding, exit code 1 when any
"""
import collections
import glob
import os
import re
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

ROOTS = ('prog/engine', 'prog/gameLibs', 'prog/daNetGame', 'prog/tools/dargbox', 'prog/1stPartyLibs/yuplay2auth', 'templates',
         '.github')
ROOT_FILES = 'make_devtools*.py'
PRUNED_DIRS = {'.git', '_output', '__pycache__', '3rdPartyLibs', 'node_modules', '.test_results'}
ANY_GAIJIN = re.compile(rb'gaijin', re.IGNORECASE)  # cheap check before decoding and scanning a file

GAIJIN_HOSTS = re.compile(r'\b(?:gaijin\.net|gaijinent\.com|gaijin\.lan)\b', re.IGNORECASE)
UPSTREAM_RELEASES = re.compile(r'\bgithub\.com/GaijinEntertainment\b', re.IGNORECASE)  # build scripts download from the fork

SLASH = ('//', '/*')
HASH = ('#',)
COMMENT_STYLES = {
  '.cpp': SLASH, '.h': SLASH, '.inl': SLASH, '.c': SLASH, '.java': SLASH, '.nut': SLASH, '.das': SLASH, '.dshl': SLASH,
  '.blk': SLASH, '.py': HASH, '.jam': HASH, '.yaml': HASH, '.yml': HASH, '.txt': (),
}

# {repo-relative path: why the hosts there are kept}; an entry must still have findings, so it is dropped once fixed
ALLOWLIST = {
  'prog/1stPartyLibs/yuplay2auth/session/yu_session.cpp':
    'log text naming the Gaijin.Net service; the endpoints are in yu_urls.h, which is not in the repo',
}

Finding = collections.namedtuple('Finding', 'path line host')


def _comment_style(rel):
  name = os.path.basename(rel)
  return HASH if name == 'jamfile' else COMMENT_STYLES.get(os.path.splitext(name)[1])


def _patterns(rel):
  is_build_script = rel.startswith('.github/') or (os.path.basename(rel).startswith('make_devtools') and '/' not in rel)
  return (GAIJIN_HOSTS, UPSTREAM_RELEASES) if is_build_script else (GAIJIN_HOSTS,)


def code_lines(text, style):
  """Text of each line with comments removed; string literals are kept, so a // inside "https://..." is not a comment."""
  line_comment = next((c for c in style if c != '/*'), None)
  block_comments = '/*' in style
  lines, cur = [], []
  quote, in_block = None, False
  i, n = 0, len(text)
  while i < n:
    c = text[i]
    if c == '\n':
      lines.append(''.join(cur))
      cur, quote = [], None
      i += 1
    elif in_block:
      if text.startswith('*/', i):
        in_block = False
        i += 2
      else:
        i += 1
    elif c == '\\' and i + 1 < n and text[i + 1] != '\n':  # escapes in strings, and jam's \# outside of them
      cur.append(text[i:i + 2])
      i += 2
    elif quote:
      cur.append(c)
      quote = None if c == quote else quote
      i += 1
    elif block_comments and text.startswith('/*', i):
      in_block = True
      i += 2
    elif line_comment and text.startswith(line_comment, i):
      end = text.find('\n', i)
      i = n if end < 0 else end
    else:
      if c in '"\'':
        quote = c
      cur.append(c)
      i += 1
  lines.append(''.join(cur))
  return lines


def scan_text(text, rel):
  style = _comment_style(rel)
  patterns = _patterns(rel)
  if style is None or not any(p.search(text) for p in patterns):
    return []
  return [Finding(rel, no, m.group(0))
          for no, line in enumerate(code_lines(text, style), 1)
          for p in patterns
          for m in p.finditer(line)]


def _source_files(engine_root):
  for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(os.path.join(engine_root, root)):
      dirnames[:] = sorted(d for d in dirnames if d not in PRUNED_DIRS)
      for name in sorted(filenames):
        yield os.path.join(dirpath, name)
  yield from sorted(glob.glob(os.path.join(engine_root, ROOT_FILES)))


def scan(engine_root=ENGINE, allowlist=None):
  allowlist = ALLOWLIST if allowlist is None else allowlist
  findings = []
  for path in _source_files(engine_root):
    rel = os.path.relpath(path, engine_root).replace(os.sep, '/')
    if rel in allowlist or _comment_style(rel) is None:
      continue
    with open(path, 'rb') as f:
      data = f.read()
    if ANY_GAIJIN.search(data):
      findings += scan_text(data.decode('utf-8', errors='replace'), rel)
  return findings


def main(argv):
  findings = scan(argv[1] if len(argv) > 1 else ENGINE)
  for f in findings:
    print('{}:{}: {}'.format(f.path, f.line, f.host))
  return 1 if findings else 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
