"""Keeps Gaijin hosts out of the fork: finds gaijin.net, gaijinent.com and gaijin.lan outside comments in the shipping code,
the tools and the build scripts, and upstream GitHub release URLs in the build scripts. It also checks that the CMake
build downloads only through prog/cmake/DagorFetch.cmake, which takes every archive from the SHA256-pinned manifest.

python host_guard.py [engine_root]  -- prints path:line: host for each finding, exit code 1 when any
"""
import collections
import glob
import os
import re
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

ROOTS = ('prog/engine', 'prog/gameLibs', 'prog/daNetGame', 'prog/tools/dargbox', 'prog/tools/pythonCommon',
         'prog/tools/toolsData', 'prog/1stPartyLibs/yuplay2auth', 'templates', '.github', 'prog/cmake')
ROOT_FILES = ('dng.py', 'CMakeLists.txt', 'CMakePresets.json')
BUILD_SCRIPTS = ('.github/', 'prog/tools/pythonCommon/dagorDevtools/', 'dng.py', 'prog/cmake/', 'CMakeLists.txt',
                 'CMakePresets.json')  # the downloads of the toolkit
PRUNED_DIRS = {'.git', '_output', '__pycache__', '3rdPartyLibs', 'node_modules', '.test_results', 'build'}
ANY_GAIJIN = re.compile(rb'gaijin', re.IGNORECASE)  # cheap check before decoding and scanning a file

GAIJIN_HOSTS = re.compile(r'\b(?:gaijin\.net|gaijinent\.com|gaijin\.lan)\b', re.IGNORECASE)
UPSTREAM_RELEASES = re.compile(r'\bgithub\.com/GaijinEntertainment\b', re.IGNORECASE)  # build scripts download from the fork
# CMake commands that download: only the fetcher may use them, so every archive is pinned in prog/cmake/sdk/manifest.cmake
CMAKE_DOWNLOADS = re.compile(r'\b(?:file\s*\(\s*DOWNLOAD|FetchContent_Declare|ExternalProject_Add)\b', re.IGNORECASE)
CMAKE_FETCHER = 'prog/cmake/DagorFetch.cmake'

SLASH = ('//', '/*')
HASH = ('#',)
COMMENT_STYLES = {
  '.cpp': SLASH, '.h': SLASH, '.inl': SLASH, '.c': SLASH, '.java': SLASH, '.nut': SLASH, '.das': SLASH, '.dshl': SLASH,
  '.blk': SLASH, '.py': HASH, '.jam': HASH, '.yaml': HASH, '.yml': HASH, '.txt': (), '.cmake': HASH, '.json': (),
}
HASH_COMMENTED_NAMES = ('jamfile', 'CMakeLists.txt')

# {repo-relative path: why the hosts there are kept}; an entry must still have findings, so it is dropped once fixed
ALLOWLIST = {
  'prog/1stPartyLibs/yuplay2auth/session/yu_session.cpp':
    'log text naming the Gaijin.Net service; the endpoints are in yu_urls.h, which is not in the repo',
}

Finding = collections.namedtuple('Finding', 'path line host')


def _comment_style(rel):
  name = os.path.basename(rel)
  return HASH if name in HASH_COMMENTED_NAMES else COMMENT_STYLES.get(os.path.splitext(name)[1])


def _patterns(rel):
  return (GAIJIN_HOSTS, UPSTREAM_RELEASES) if rel.startswith(BUILD_SCRIPTS) else (GAIJIN_HOSTS,)


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


def _is_cmake(rel):
  return rel.endswith('.cmake') or os.path.basename(rel) == 'CMakeLists.txt'


def scan_downloads(text, rel):
  """Downloads in CMake code outside the fetcher, which would bypass the pinned manifest."""
  if not _is_cmake(rel) or rel == CMAKE_FETCHER or not CMAKE_DOWNLOADS.search(text):
    return []
  return [Finding(rel, no, m.group(0))
          for no, line in enumerate(code_lines(text, HASH), 1)
          for m in CMAKE_DOWNLOADS.finditer(line)]


def _source_files(engine_root):
  for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(os.path.join(engine_root, root)):
      dirnames[:] = sorted(d for d in dirnames if d not in PRUNED_DIRS)
      for name in sorted(filenames):
        yield os.path.join(dirpath, name)
  for name in ROOT_FILES:
    yield from glob.glob(os.path.join(engine_root, name))


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
    if _is_cmake(rel):
      findings += scan_downloads(data.decode('utf-8', errors='replace'), rel)
  return findings


def main(argv):
  findings = scan(argv[1] if len(argv) > 1 else ENGINE)
  for f in findings:
    print('{}:{}: {}'.format(f.path, f.line, f.host))
  return 1 if findings else 0


if __name__ == '__main__':
  sys.exit(main(sys.argv))
