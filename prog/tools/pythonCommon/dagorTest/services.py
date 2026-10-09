"""Services started for targets that declare them in requires:t= (see manifest.REQUIREMENTS)."""
import os
import socket
import sys
import time

from . import process


# python -m http.server, except HTTPServer.server_bind resolves the host name before listening: on macOS CI runners
# that reverse lookup takes longer than START_TIMEOUT
_HTTP_SERVER = '''
import functools, http.server, socketserver, sys
class Server(http.server.ThreadingHTTPServer):
  def server_bind(self):
    socketserver.TCPServer.server_bind(self)
    self.server_name, self.server_port = self.server_address[:2]
port, root = int(sys.argv[1]), sys.argv[2]
server = Server(('127.0.0.1', port), functools.partial(http.server.SimpleHTTPRequestHandler, directory=root))
print('serving {} at http://127.0.0.1:{}/'.format(root, port), flush=True)
server.serve_forever()
'''


def _free_port():
  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('127.0.0.1', 0))
    return s.getsockname()[1]


class HttpServer:
  """Serves an empty writable directory over HTTP for one target (unittest::http_service in dag_testEnv.h)."""

  START_TIMEOUT = 15.0

  def __init__(self, root_dir: str, log_path: str):
    self.root_dir = os.path.abspath(root_dir)
    self.log_path = log_path
    self.port = None
    self.proc = None
    self.log = None

  def __enter__(self):
    os.makedirs(self.root_dir, exist_ok=True)
    os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
    self.log = open(self.log_path, 'wb')
    for _ in range(5):  # the port may be taken between probing and binding
      self.port = _free_port()
      self.proc = process.start([sys.executable, '-c', _HTTP_SERVER, str(self.port), self.root_dir], cwd=self.root_dir, log_file=self.log)
      if self._wait_listening():
        return self
      process.kill_tree(self.proc)
    self.__exit__(None, None, None)
    raise RuntimeError('cannot start the HTTP test server, see {}'.format(self.log_path))

  def _wait_listening(self):
    deadline = time.monotonic() + self.START_TIMEOUT
    while time.monotonic() < deadline:
      if self.proc.poll() is not None:
        return False
      try:
        with socket.create_connection(('127.0.0.1', self.port), timeout=0.5):
          return True
      except OSError:
        time.sleep(0.05)
    return False

  def env(self):
    return {'DAGOR_TEST_HTTP_URL': 'http://127.0.0.1:{}/'.format(self.port), 'DAGOR_TEST_HTTP_ROOT': self.root_dir.replace('\\', '/')}

  def __exit__(self, *exc):
    if self.proc:
      process.kill_tree(self.proc)
      self.proc = None
    if self.log:
      self.log.close()
      self.log = None
    return False
