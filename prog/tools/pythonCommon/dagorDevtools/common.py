"""What the host setups of dng.py devtools share: the toolkit dir, downloads, links, unpacking, python, jam and
prog/platform.jam."""
import os
import pathlib
import ssl
import subprocess
import sys
import tarfile
import zipfile
from urllib import request

from ..dagorBuild import ENGINE_ROOT

WINDOWS = sys.platform.startswith('win')
JAM_RELEASE = 'https://github.com/Prose-Studio/DagorEngine/releases/download/2.5-G8-1.3-2024%2F04%2F01/'
FMOD = 'fmod-studio-2.xx.xx'

ssl._create_default_https_context = ssl._create_unverified_context

# unattended runs (CI, DAGOR_NONINTERACTIVE=1, no terminal) take the default answer instead of prompting
NONINTERACTIVE = os.environ.get('DAGOR_NONINTERACTIVE', '') == '1' or not sys.stdin.isatty()


def error(s):
  sys.exit('\nERROR: {0}\n'.format(s))


def ask(s, unattended_answer):
  if NONINTERACTIVE:
    print("\n{0} [{1}, non-interactive]".format(s, 'yes' if unattended_answer else 'no'))
    return unattended_answer
  while True:
    try:
      answer = input("\n{0} [Y/n]: ".format(s)).strip().lower()
    except EOFError:  # stdin is NUL or a closed pipe (isatty() is true for NUL on Windows)
      print('[{0}, no input]'.format('yes' if unattended_answer else 'no'))
      return unattended_answer
    if answer in ('y', 'yes', ''):
      return True
    if answer in ('n', 'no'):
      return False


def run(cmd, cwd=None):
  try:
    print("Running: {0}".format(cmd))
    subprocess.run(cmd, shell = True, check = True, cwd = cwd)
  except subprocess.CalledProcessError as e:
    print("subprocess.run failed with a non-zero exit code. Error: {0}".format(e))
  except OSError as e:
    print("An OSError occurred, subprocess.run command may have failed. Error: {0}".format(e))


def pip_install(python):
  subprocess.run([python, '-m', 'pip', 'install', '--upgrade', 'pip'])
  subprocess.run([python, '-m', 'pip', '--version'])
  subprocess.run([python, '-m', 'pip', 'install', 'clang==14.0.6'])
  subprocess.run([python, '-m', 'pip', 'install', 'cymbal'])


class Devtools:
  """The toolkit dir: dest, with the downloaded packages in dest/.packages."""

  def __init__(self, dest):
    self.dest = dest.replace('\\', '/').rstrip('/')
    if ' ' in self.dest:
      error("The destination directory contains spaces, which are not allowed in a file path.")
    if not self.dest.isascii():
      error("The destination directory contains non-ASCII characters.")
    if not os.path.isabs(self.dest):
      error("The destination directory must be an absolute path.")
    pathlib.Path(self.dest + '/.packages').mkdir(parents=True, exist_ok=True)

  def path(self, name):
    return self.dest + '/' + name

  def exists(self, name):
    return pathlib.Path(self.path(name)).exists()

  def download(self, url, file=None):
    """.packages/<file> (by default the file name of the url), downloaded unless it is there already."""
    file = self.path('.packages/' + (file or url.rsplit('/', 1)[1]))
    if pathlib.Path(file).exists():
      print("Package '{0}' already exists".format(file))
      return file
    print("Downloading '{0}' to '{1}' ...".format(url, file))
    pathlib.Path(file).parent.mkdir(parents=True, exist_ok=True)
    request.urlretrieve(url, file + '.part')  # an interrupted download is not mistaken for a complete one
    os.replace(file + '.part', file)
    return file

  def link_dir(self, src, dest):
    """dest becomes a link to the src dir (a junction on Windows)."""
    src, dest = os.path.normpath(src), os.path.normpath(dest)
    try:
      if WINDOWS:
        subprocess.run(['cmd', '/C', 'mklink', '/J', dest, src], check = True)
      else:
        os.symlink(src, dest)
    except (subprocess.CalledProcessError, OSError) as e:
      error("Symlink failed. Error: {0}, Source = '{1}', Destination = '{2}'".format(e, src, dest))

  def unpack(self, package, to):
    if package.endswith('.zip'):
      with zipfile.ZipFile(os.path.normpath(package), 'r') as zip_file:
        zip_file.extractall(to)
    else:
      with tarfile.open(os.path.normpath(package), 'r:gz') as tar_file:
        tar_file.extractall(to)

  def link_python(self):
    """dest/python3: the dir of the running python (Linux, macOS)."""
    python_dest_folder = self.path('python3')
    if pathlib.Path(python_dest_folder).exists():
      print('=== Python 3 symlink found at {0}, skipping setup'.format(python_dest_folder))
      return
    python_src_folder = os.path.dirname(sys.executable)
    print('+++ Python 3 found at {0}'.format(python_src_folder))
    self.link_dir(python_src_folder, python_dest_folder)
    pip_install(sys.executable)

  def install_astcenc(self, zip_name, platform_dir):
    astcenc_dest_folder = self.path('astcenc-4.6.1')
    if pathlib.Path(astcenc_dest_folder).exists():
      print('=== ASTC encoder 4.6.1 {0}, skipping setup'.format(astcenc_dest_folder))
      return
    self.unpack(self.download('https://github.com/ARM-software/astc-encoder/releases/download/4.6.1/' + zip_name),
                astcenc_dest_folder)
    os.rename(os.path.normpath(astcenc_dest_folder + '/bin'), os.path.normpath(astcenc_dest_folder + '/' + platform_dir))
    if not WINDOWS:
      run('chmod 755 {0}/{1}/astcenc*'.format(astcenc_dest_folder, platform_dir))
    print('+++ ASTC encoder 4.6.1 installed at {0}'.format(astcenc_dest_folder))

  def install_ispc(self, archive, folder):
    ispc_dest_folder = self.path(folder)
    if pathlib.Path(ispc_dest_folder).exists():
      print('=== ISPC v1.23.0 {0}, skipping setup'.format(ispc_dest_folder))
      return
    self.unpack(self.download('https://github.com/ispc/ispc/releases/download/v1.23.0/' + archive), self.dest)
    print('+++ ISPC v1.23.0 installed at {0}'.format(ispc_dest_folder))

  def install_jam(self, asset):
    """jam from the fork's release unless one is on PATH; outside Windows it is copied to /usr/local/bin."""
    try:
      subprocess.run(['jam', '-v'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      return
    except FileNotFoundError:
      pass
    print("jam not found, installing jam...")
    self.unpack(self.download(JAM_RELEASE + asset), self.dest)
    if not WINDOWS:
      run('chmod 755 ' + self.path('jam'))
      print('--- will copy jam to /usr/local/bin using sudo:')
      run('sudo cp {0} /usr/local/bin/jam'.format(self.path('jam')))

  def write_platform_jam(self, extra_lines):
    with open(os.path.join(ENGINE_ROOT, 'prog', 'platform.jam'), 'w') as fd:
      fd.write('_DEVTOOL = {0} ;\n'.format(self.dest))
      fd.write('FmodStudio = 2.xx.xx ;\n' if self.exists(FMOD + '/LICENSE.TXT') else 'FmodStudio = none ;\n')
      for line in extra_lines:
        fd.write(line + '\n')
