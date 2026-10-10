#!/usr/bin/env python3
"""Runs a test command with an HTTP server for it (tests that REQUIRES http_server, see DagorTesting.cmake).

python run_with_http_server.py <work dir> <command>...

The server serves a new empty dir under <work dir> on a free local port; the command gets its URL and dir in
DAGOR_TEST_HTTP_URL and DAGOR_TEST_HTTP_ROOT (unittest::http_service in dag_testEnv.h). The exit code is the command's.
"""
import functools
import http.server
import os
import socketserver
import subprocess
import sys
import tempfile
import threading


class Server(http.server.ThreadingHTTPServer):
  def server_bind(self):
    # HTTPServer.server_bind resolves the host name before listening, which can take seconds (macOS CI runners)
    socketserver.TCPServer.server_bind(self)
    self.server_name, self.server_port = self.server_address[:2]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
  def log_message(self, format, *args):
    pass


def main(argv):
  if len(argv) < 2:
    sys.exit(__doc__)
  work_dir, command = argv[0], argv[1:]
  os.makedirs(work_dir, exist_ok=True)
  root = tempfile.mkdtemp(prefix='http_root_', dir=work_dir)
  server = Server(('127.0.0.1', 0), functools.partial(QuietHandler, directory=root))
  thread = threading.Thread(target=server.serve_forever, daemon=True)
  thread.start()
  env = dict(os.environ)
  env['DAGOR_TEST_HTTP_URL'] = 'http://127.0.0.1:{}/'.format(server.server_port)
  env['DAGOR_TEST_HTTP_ROOT'] = root.replace('\\', '/')
  try:
    return subprocess.run(command, env=env).returncode
  finally:
    server.shutdown()
    server.server_close()


if __name__ == '__main__':
  sys.exit(main(sys.argv[1:]))
