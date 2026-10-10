"""dng.py devtools: downloads, installs and links the build toolkit (compilers, SDKs, jam) into one directory.

Steps that are done already are skipped, so it is safe to run again (after a toolkit update, or into the same dir from
another checkout). It writes prog/platform.jam (_DEVTOOL = <dir>) and, on Windows, offers to point GDEVTOOL and the
user PATH at the dir (unattended runs leave them alone).
"""
import argparse
import sys

from .common import Devtools

EPILOG = '''examples:
  python dng.py devtools X:/develop/devtools
  python3 dng.py devtools ~/devtools'''


def main(argv):
  p = argparse.ArgumentParser(prog='dng.py devtools', description=__doc__, epilog=EPILOG,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
  p.add_argument('dest', help='the toolkit dir: an absolute path without spaces or non-ASCII characters, created when missing')
  args = p.parse_args(argv)
  if sys.platform.startswith('win'):
    from . import windows as host
  elif sys.platform.startswith('darwin'):
    from . import macos as host
  elif sys.platform.startswith('linux'):
    from . import linux as host
  else:
    p.error('unsupported platform {}'.format(sys.platform))

  d = Devtools(args.dest)
  d.write_platform_jam(host.setup(d))
  env_updated = host.finish(d)
  print("\nDone." + (" Please restart your command-line environment to apply the environment variables." if env_updated else ""))
  return 0
