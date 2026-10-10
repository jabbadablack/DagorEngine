"""Tests of host_guard: the comment-aware scanner, and the engine tree itself having no Gaijin hosts."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import host_guard  # noqa: E402


def hosts(text, rel='prog/engine/a.cpp'):
  return [(f.line, f.host) for f in host_guard.scan_text(text, rel)]


class ScannerTest(unittest.TestCase):
  def test_url_in_a_string_is_found(self):
    self.assertEqual(hosts('const char *u = "https://support.gaijin.net/x";'), [(1, 'gaijin.net')])

  def test_slashes_inside_a_string_do_not_start_a_comment(self):
    self.assertEqual(hosts('a = "http://x"; b = "https://gaijinent.com"; // gaijin.lan'), [(1, 'gaijinent.com')])

  def test_line_and_block_comments_are_ignored(self):
    self.assertEqual(hosts('// gaijin.lan docs\nint a; /* gaijin.net\n gaijinent.com */ int b = 0;\nc("gaijin.net");'),
                     [(4, 'gaijin.net')])

  def test_hash_comments(self):
    self.assertEqual(hosts('# gaijin.net\nx = "gaijin.net"  # gaijin.lan', 'prog/tools/pythonCommon/dagorDevtools/windows.py'),
                     [(2, 'gaijin.net')])
    self.assertEqual(hosts('x = \\# gaijin.net ;', 'prog/daNetGame/jamfile'), [(1, 'gaijin.net')])

  def test_java_packages_are_not_hosts(self):
    self.assertEqual(hosts('package com.gaijinent.common;', 'prog/engine/a.java'), [])

  def test_upstream_releases_only_in_build_scripts(self):
    url = 'u = "https://github.com/GaijinEntertainment/jam/releases"'
    self.assertEqual(hosts(url, 'prog/tools/pythonCommon/dagorDevtools/linux.py'), [(1, 'github.com/GaijinEntertainment')])
    self.assertEqual(hosts(url, '.github/workflows/tests.yaml'), [(1, 'github.com/GaijinEntertainment')])
    self.assertEqual(hosts(url, 'prog/engine/a.py'), [])

  def test_unknown_file_types_are_skipped(self):
    self.assertEqual(hosts('gaijin.net', 'prog/engine/a.png'), [])


class TreeTest(unittest.TestCase):
  def test_no_gaijin_hosts_outside_comments(self):
    findings = ['{}:{}: {}'.format(*f) for f in host_guard.scan()]
    self.assertEqual(findings, [], 'add the code to host_guard.ALLOWLIST only if the host must stay')

  def test_allowlist_entries_still_have_findings(self):
    for rel in host_guard.ALLOWLIST:
      with open(os.path.join(host_guard.ENGINE, rel), encoding='utf-8', errors='replace') as f:
        self.assertTrue(host_guard.scan_text(f.read(), rel), '{} has no hosts left, remove it from ALLOWLIST'.format(rel))


if __name__ == '__main__':
  unittest.main()
