#!/usr/bin/env python3
"""A first CMakeLists.txt for a jamfile, for the port to CMake (deleted together with jam).

It translates the common subset of jamfiles: the target variables (Target, TargetType, Sources, AddIncludes,
UseProgLibs, CPPopt, AddLibs, ...), 'opt on <file>', Autoscan source dirs, and 'if' on Platform, PlatformArch,
KernelLinkage, PlatformSpec, SSEVersion and Sanitize. Branches only consoles take are dropped. What it cannot translate
is kept as '# TODO(jam): <statement>' at its place, to be ported by hand (the CI lint fails on TODO(jam) in ported dirs).

python skeleton.py <jamfile>... [--write] [--force]   -- prints the CMakeLists.txt, or writes it next to the jamfile
"""
import argparse
import os
import re
import sys

ENGINE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))

CONSOLES = {'ps4', 'ps5', 'xboxOne', 'scarlett', 'nswitch'}
PLATFORMS = {'windows', 'linux', 'macOS', 'iOS', 'tvOS', 'android'}
ARCHS = {'x86_64': 'x86_64', 'arm64': 'arm64', 'arm64-v8a': 'arm64', 'e2k': 'e2k'}
CONDITION_VARS = {'Platform': 'DAGOR_PLATFORM', 'PlatformArch': 'DAGOR_ARCH', 'KernelLinkage': 'DAGOR_KERNEL_LINKAGE',
                  'SSEVersion': 'DAGOR_SSE', 'Sanitize': 'DAGOR_SANITIZE', 'PlatformSpec': 'DAGOR_CC'}
LIST_VARS = {'Sources': 'sources', 'AddIncludes': 'includes', 'UseProgLibs': 'deps', 'CPPopt': 'cpp_opt',
             'Copt': 'c_opt', 'AddLibs': 'libs', 'LINKopt': 'link_options'}
SCALAR_VARS = {'Location', 'Target', 'TargetType', 'StrictCompile', 'ConsoleExe', 'OutDir', 'Exceptions', 'Rtti',
               'Root'}
KNOWN_INCLUDES = {'defaults.jam', 'build.jam', 'unitTest.jam'}
# jam variables that only ever had their defaults.jam value; CMake builds have just that version
FIXED_VERSIONS = {'UseZlibVer': 'ng', 'ZstdVer': '1.4.5', 'OpenSSLVer': '3.x', 'DefOpenSSLVer': '3.x', 'BulletSdkVer': '3',
                  'DefBulletSdkVer': '3', 'FreeTypeVer': '2.8', 'DefFreeTypeVer': '2.8', 'OpenXrVer': '1.1.54',
                  'CPPStd': '20'}


# --- lexer -----------------------------------------------------------------------------------------------------------
def tokens(text):
  """(token, line) of a jamfile: whitespace-separated, '#' comments, "quoted" parts kept with their quotes."""
  out = []
  i, n, line = 0, len(text), 1
  while i < n:
    c = text[i]
    if c == '\n':
      line += 1
      i += 1
    elif c.isspace():
      i += 1
    elif c == '#':
      while i < n and text[i] != '\n':
        i += 1
    else:
      start, start_line, quoted = i, line, False
      while i < n and (quoted or not text[i].isspace()):
        if text[i] == '\\' and i + 1 < n:
          i += 2
          continue
        if text[i] == '"':
          quoted = not quoted
        if text[i] == '\n':
          line += 1
        i += 1
      out.append((text[start:i], start_line))
  return out


# --- parser ----------------------------------------------------------------------------------------------------------
class Parser:
  """Statements as tuples: ('assign', var, op, values, src), ('on', var, target, op, values, src),
  ('include', path, src), ('if', [(cond, block)...], else_block, src), ('other', src)."""

  def __init__(self, toks):
    self.toks = toks
    self.i = 0

  def peek(self, k=0):
    return self.toks[self.i + k][0] if self.i + k < len(self.toks) else None

  def next(self):
    t = self.toks[self.i][0]
    self.i += 1
    return t

  def until_semicolon(self):
    words = []
    while self.peek() not in (';', None):
      words.append(self.next())
    if self.peek() == ';':
      self.next()
    return words

  def block(self):
    stmts = []
    while self.peek() not in ('}', None):
      stmts.append(self.statement())
    if self.peek() == '}':
      self.next()
    return stmts

  def skip_braced(self):
    """The text of a { ... } construct the converter does not translate."""
    words, depth = [], 0
    while self.peek() is not None:
      t = self.next()
      words.append(t)
      if t == '{':
        depth += 1
      elif t == '}':
        depth -= 1
        if depth == 0:
          break
    return words

  def statement(self):
    t = self.peek()
    if t == 'if':
      self.next()
      branches, else_block = [], None
      cond = []
      while self.peek() != '{':
        cond.append(self.next())
      self.next()
      branches.append((cond, self.block()))
      while self.peek() == 'else':
        self.next()
        if self.peek() == 'if':
          self.next()
          cond = []
          while self.peek() != '{':
            cond.append(self.next())
          self.next()
          branches.append((cond, self.block()))
        else:
          self.next()  # {
          else_block = self.block()
          break
      return ('if', branches, else_block)
    if t == 'include':
      self.next()
      words = self.until_semicolon()
      return ('include', ' '.join(words), 'include ' + ' '.join(words) + ' ;')
    if t in ('for', 'switch', 'rule', 'while', 'actions'):
      return ('other', ' '.join(self.skip_braced()))
    if t == 'local':
      words = self.until_semicolon()
      return ('other', ' '.join(words) + ' ;')
    if t == '{':
      self.next()
      return ('if', [(['1'], self.block())], None)
    # assignment, 'on' assignment or a rule call
    if self.peek(1) in ('=', '+=', '?=', '-='):
      var, op = self.next(), self.next()
      return ('assign', var, op, self.until_semicolon())
    if self.peek(1) == 'on' and self.peek(3) in ('=', '+='):
      var = self.next()
      self.next()
      target, op = self.next(), self.next()
      return ('on', var, target, op, self.until_semicolon())
    words = self.until_semicolon()
    return ('other', ' '.join(words) + ' ;')

  def parse(self):
    stmts = []
    while self.peek() is not None:
      if self.peek() == '}':
        self.next()
        continue
      stmts.append(self.statement())
    return stmts


# --- translation -----------------------------------------------------------------------------------------------------
class Untranslatable(Exception):
  pass


def value(word, kind):
  """A jam word as a CMake list item; Untranslatable for variables it does not know."""
  w = word
  w = w.replace('$(Root)/prog/', '${DAGOR_PROG_DIR}/').replace('$(Root)/', '${DAGOR_ENGINE_ROOT}/')
  w = re.sub(r'^\$\(Location\)/', '', w)
  w = w.replace('$(Platform)', '${DAGOR_PLATFORM}').replace('$(PlatformArch)', '${DAGOR_ARCH}')
  for var, fixed in FIXED_VERSIONS.items():
    w = w.replace('$({})'.format(var), fixed)
  if '$(' in w or '[' in w:
    raise Untranslatable(word)
  if kind == 'deps' and w.startswith('${DAGOR_PROG_DIR}/'):
    w = w[len('${DAGOR_PROG_DIR}/'):]
  return w


def split_cpp_opt(words):
  """(defines, options) of CPPopt words."""
  defines, options = [], []
  for w in words:
    if w.startswith('-D'):
      d = w[2:].replace('\\\\\\"', '"').replace('\\"', '"')
      defines.append(d if not re.search(r'[\s;"]', d) else '"' + d.replace('"', '\\"') + '"')
    else:
      options.append(w)
  return defines, options


def cmake_values(values, depth=0, head=''):
  """the values on the line, or one per line when they do not fit"""
  line = ' '.join(values)
  if len(head) + len(line) + 2 * depth <= 110:
    return line
  return '\n' + '\n'.join('  ' * (depth + 1) + v for v in values) + '\n' + '  ' * depth


def condition(words):
  """A jam condition as a CMake if() expression, or 'FALSE'/'TRUE' when it only depends on consoles."""
  expr, i = [], 0

  def operand(w):
    m = re.fullmatch(r'\$\((\w+)\)', w)
    if m:
      var = m.group(1)
      if var not in CONDITION_VARS:
        raise Untranslatable(w)
      return ('var', var)
    if '$(' in w:
      if re.fullmatch(r'\$\(Platform\)-\$\(PlatformArch\)', w):
        return ('var', 'Platform-PlatformArch')
      raise Untranslatable(w)
    return ('lit', w.strip('"'))

  def cvar(var):
    if var == 'Platform-PlatformArch':
      return '"${DAGOR_PLATFORM}-${DAGOR_ARCH}"'
    return CONDITION_VARS[var]

  def norm(var, lit):
    """the CMake value of a jam value, None when no supported target has it"""
    if var == 'Platform':
      return lit if lit in PLATFORMS else None
    if var == 'PlatformArch':
      return ARCHS.get(lit)
    if var == 'Platform-PlatformArch':
      p, _, a = lit.partition('-')
      return '{}-{}'.format(p, ARCHS[a]) if p in PLATFORMS and a in ARCHS else None
    if var == 'Sanitize':
      return 'none' if lit == 'disabled' else lit
    if var == 'PlatformSpec':
      return {'clang': 'clang', 'gcc': 'gcc', 'vc17': 'msvc', 'vc16': 'msvc', 'msvc': 'msvc'}.get(lit)
    return lit

  def term(a, op, rest):
    kind, var = a
    if kind != 'var':
      raise Untranslatable(a[1])
    lits = [norm(var, lit) for lit in rest]
    if var == 'PlatformSpec' and 'clang' in lits:
      lits += ['clang-cl']
    lits = sorted({l for l in lits if l is not None})
    if op in ('=', 'in'):
      if not lits:
        return 'FALSE'
      if len(lits) == 1:
        return '{} STREQUAL "{}"'.format(cvar(var), lits[0])
      return '{} MATCHES "^({})$"'.format(cvar(var), '|'.join(re.escape(l) for l in lits))
    if op == '!=':
      if not lits:
        return 'TRUE'
      return 'NOT {} STREQUAL "{}"'.format(cvar(var), lits[0])
    raise Untranslatable(op)

  while i < len(words):
    w = words[i]
    if w in ('&&', '||'):
      expr.append('AND' if w == '&&' else 'OR')
      i += 1
    elif w == '!':
      expr.append('NOT')
      i += 1
    elif w in ('(', ')'):
      expr.append(w)
      i += 1
    else:
      a = operand(w)
      op = words[i + 1] if i + 1 < len(words) else None
      if op in ('=', '!='):
        expr.append(term(a, op, [words[i + 2]]))
        i += 3
      elif op == 'in':
        j = i + 2
        lits = []
        while j < len(words) and words[j] not in ('&&', '||', ')'):
          lits.append(operand(words[j])[1])
          j += 1
        expr.append(term(a, 'in', lits))
        i = j
      else:
        if a[0] == 'lit' and a[1] == '1':
          expr.append('TRUE')
        elif a[0] == 'var':
          expr.append(cvar(a[1]))
        else:
          raise Untranslatable(w)
        i += 1
  text = ' '.join(expr)
  return text


class Converter:
  def __init__(self, jamfile):
    self.jamfile = jamfile
    self.lines = []
    self.scalars = {}
    self.used = set()
    self.after_build = False
    self.todo = 0

  def emit(self, depth, text):
    self.lines.append('  ' * depth + text.replace(' \n', '\n'))

  def todo_line(self, depth, src):
    self.todo += 1
    for i, part in enumerate(re.findall(r'.{1,100}(?:\s|$)', src.strip()) or [src]):
      self.emit(depth, ('# TODO(jam): ' if i == 0 else '#   ') + part.strip())

  def assign(self, depth, var, op, values, src):
    if var in LIST_VARS:
      name = LIST_VARS[var]
      try:
        if name == 'cpp_opt':
          defines, options = split_cpp_opt(values)
          items = [('defines', defines), ('options', [value(o, 'options') for o in options])]
        elif name == 'c_opt':
          items = [('c_options', [value(o, 'options') for o in values])]
        else:
          items = [(name, [value(v, name) for v in values])]
      except Untranslatable:
        self.todo_line(depth, src)
        return
      for name, vals in items:
        if not vals and (op != '=' or name not in self.used):
          continue
        if op == '+=' or (op == '?=' and name in self.used):
          head = 'list(APPEND {} '.format(name)
          self.emit(depth, head + cmake_values(vals, depth, head) + ')')
        elif vals:
          head = 'set({} '.format(name)
          self.emit(depth, head + cmake_values(vals, depth, head) + ')')
        else:
          self.emit(depth, 'set({})'.format(name))
        self.used.add(name)
      return
    if var in SCALAR_VARS and depth == 0 and op in ('=', '?='):
      self.scalars[var] = values
      return
    if var in ('AllSrcFolder_CPP', 'AllSrcFolder_C'):
      try:
        self.emit(depth, 'list(APPEND source_dirs {})'.format(cmake_values([value(v, 'dirs') for v in values])))
        self.used.add('source_dirs')
      except Untranslatable:
        self.todo_line(depth, src)
      return
    self.todo_line(depth, src)

  def statements(self, stmts, depth):
    for s in stmts:
      kind = s[0]
      if kind == 'assign':
        _, var, op, values = s
        self.assign(depth, var, op, values, '{} {} {} ;'.format(var, op, ' '.join(values)))
      elif kind == 'on':
        _, var, target, op, values = s
        src = '{} on {} {} {} ;'.format(var, target, op, ' '.join(values))
        if var in ('opt', 'CPPopt') and '$(' not in target:
          self.emit(depth, 'list(APPEND source_options {} {})'.format(target, cmake_values(values)))
          self.used.add('source_options')
        else:
          self.todo_line(depth, src)
      elif kind == 'include':
        _, path, src = s
        base = os.path.basename(path)
        if base in KNOWN_INCLUDES:
          if base == 'unitTest.jam':
            self.scalars['unitTest'] = True
          if base == 'build.jam':
            self.after_build = True
        else:
          self.todo_line(depth, src)
      elif kind == 'if':
        _, branches, else_block = s
        emitted = False
        try:
          conds = [condition(c) for c, _ in branches]
        except Untranslatable:
          self.todo_line(depth, self.source_of(s))
          continue
        for (cond_words, block), cond in zip(branches, conds):
          if cond == 'FALSE':
            continue
          if cond == 'TRUE' and not emitted:
            self.statements(block, depth)
            else_block = None
            emitted = None
            break
          self.emit(depth, ('elseif({})' if emitted else 'if({})').format(cond))
          self.statements(block, depth + 1)
          emitted = True
        if emitted is None:
          continue
        if else_block:
          if emitted:
            self.emit(depth, 'else()')
            self.statements(else_block, depth + 1)
          else:
            self.statements(else_block, depth)
        if emitted:
          self.emit(depth, 'endif()')
      else:
        self.todo_line(depth, s[1])

  def source_of(self, s):
    def text(stmts):
      out = []
      for st in stmts:
        if st[0] == 'assign':
          out.append('{} {} {} ;'.format(st[1], st[2], ' '.join(st[3])))
        elif st[0] == 'on':
          out.append('{} on {} {} {} ;'.format(st[1], st[2], st[3], ' '.join(st[4])))
        elif st[0] == 'if':
          out.append(self.source_of(st))
        else:
          out.append(st[-1])
      return ' '.join(out)
    _, branches, else_block = s
    parts = []
    for n, (cond, block) in enumerate(branches):
      parts.append('{}if {} {{ {} }}'.format('else ' if n else '', ' '.join(cond), text(block)))
    if else_block:
      parts.append('else {{ {} }}'.format(text(else_block)))
    return ' '.join(parts)

  def call(self):
    s = self.scalars
    type_ = (s.get('TargetType') or ['lib'])[0]
    target = (s.get('Target') or [''])[0]
    name = os.path.splitext(os.path.basename(re.sub(r'\$\([^)]*\)', '', target)))[0].rstrip('-~')
    args = []
    if s.get('StrictCompile') == ['yes']:
      args.append('STRICT')
    if s.get('ConsoleExe') == ['yes'] or s.get('unitTest'):
      args.append('CONSOLE')
    for var, prop in (('Exceptions', 'EXCEPTIONS'), ('Rtti', 'RTTI')):
      if s.get(var) in (['yes'], ['no']):
        args.append('{} {}'.format(prop, 'ON' if s[var] == ['yes'] else 'OFF'))
    if 'OutDir' in s:
      try:
        args.append('OUTPUT_DIR ' + value(s['OutDir'][0], 'dirs'))
      except Untranslatable:
        self.todo_line(0, 'OutDir = {} ;'.format(' '.join(s['OutDir'])))
    for var, kw in (('sources', 'SOURCES'), ('source_dirs', 'SOURCE_DIRS'), ('includes', 'PRIVATE_INCLUDES'),
                    ('defines', 'PRIVATE_DEFINES'), ('options', 'COMPILE_OPTIONS'), ('c_options', 'C_OPTIONS'),
                    ('source_options', 'SOURCE_OPTIONS'), ('deps', 'DEPS'), ('libs', 'SYSTEM_LIBS'),
                    ('link_options', 'LINK_OPTIONS')):
      if var in self.used:
        args.append('{} ${{{}}}'.format(kw, var))
    if s.get('unitTest'):
      head = 'dagor_add_catch2_test({}'.format(name)
    elif type_ == 'exe':
      head = 'dagor_add_executable({}'.format(name)
    elif type_ == 'dll':
      head = 'dagor_add_shared_library({}'.format(name)
    else:
      head = 'dagor_add_library('
      lib_name = os.path.splitext(target)[0]
      location = (s.get('Location') or [''])[0]
      if lib_name and location and '$(' not in lib_name and lib_name != location[len('prog/'):]:
        self.emit(0, '# jam named the library {}; dependents use the directory name'.format(target))
    sep = '' if head.endswith('(') else ' '
    if len(head) + 1 + sum(len(a) + 1 for a in args) <= 118:
      self.emit(0, head + sep + ' '.join(args) + ')')
    else:
      self.emit(0, head + sep + args[0] if args else head)
      for a in args[1:]:
        self.emit(1, a)
      self.emit(0, ')')

  def convert(self, text):
    stmts = Parser(tokens(text)).parse()
    body_start = len(self.lines)
    self.statements(stmts, 0)
    self.lines.append('')
    self.call()
    rel = os.path.relpath(self.jamfile, ENGINE).replace(os.sep, '/')
    header = ['# Ported from {} (jam2cmake/skeleton.py{})'.format(
      rel, '; {} TODO(jam) to port by hand'.format(self.todo) if self.todo else '')]
    return '\n'.join(header + self.lines[body_start:]).replace('\n\n\n', '\n\n') + '\n'


def main(argv):
  parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
  parser.add_argument('jamfiles', nargs='+')
  parser.add_argument('--write', action='store_true', help='write CMakeLists.txt next to the jamfile')
  parser.add_argument('--force', action='store_true', help='overwrite an existing CMakeLists.txt')
  args = parser.parse_args(argv)
  status = 0
  for jamfile in args.jamfiles:
    with open(jamfile, encoding='utf-8', errors='replace') as f:
      out = Converter(os.path.abspath(jamfile)).convert(f.read())
    if not args.write:
      sys.stdout.write(out)
      continue
    dest = os.path.join(os.path.dirname(jamfile), 'CMakeLists.txt')
    if os.path.exists(dest) and not args.force:
      print('{} exists, skipped (--force overwrites)'.format(dest), file=sys.stderr)
      status = 1
      continue
    with open(dest, 'w', newline='\n') as f:
      f.write(out)
    print(dest)
  return status


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
