"""iOS backend (simulator via `xcrun simctl`, devices via `xcrun devicectl`). UNVERIFIED: not yet run on a Mac.

What a working backend has to do (see base.DeviceBackend):
  available  macOS host with Xcode: `xcrun simctl list devices booted` (or `xcrun devicectl list devices`) shows the
             selected device (--device ios[:<udid>])
  deploy     an iOS test executable is an app bundle: `xcrun simctl install <udid> <bundle.app>`, data dir copied into
             the app's data container (`xcrun simctl get_app_container <udid> <bundle id> data`)
  run        `xcrun simctl launch --console-pty --terminate-running-process <udid> <bundle id> <args>` streams the output
             until the app exits; on devices `xcrun devicectl device process launch --console`
  exit code  not reported by launch: read the final {"event":"exit","code":N} of events.jsonl after collect()
  collect    copy the work dir back out of the data container
  cleanup    `xcrun simctl uninstall <udid> <bundle id>`
"""
import shutil
import subprocess
import sys

from .base import DeviceBackend

NOT_VERIFIED = ('the iOS device backend is not implemented yet: it needs a Mac with Xcode to be verified on '
                '(see prog/tools/pythonCommon/dagorTest/devices/ios.py for what it has to do)')


class IosDevice(DeviceBackend):
  name = 'ios'
  platforms = ['iOS']

  def available(self) -> bool:
    if sys.platform != 'darwin' or not shutil.which('xcrun'):
      return False
    try:
      out = subprocess.run(['xcrun', 'simctl', 'list', 'devices', 'booted'], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
      return False
    return '(Booted)' in out and (not self.device_id or self.device_id in out)

  def deploy(self, ctx, exe, data_dir, host_work_dir):
    raise NotImplementedError(NOT_VERIFIED)

  def remote_path(self, deployed, host_path):
    raise NotImplementedError(NOT_VERIFIED)

  def run(self, deployed, args, env, timeout, log_path):
    raise NotImplementedError(NOT_VERIFIED)
