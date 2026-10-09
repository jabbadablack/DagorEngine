"""Android device backend (adb). UNVERIFIED: designed against adb's documented behavior, not yet run on a device.

What a working backend has to do (see base.DeviceBackend):
  available  `adb devices` lists the selected device (--device android[:<serial>]) in state "device"
  deploy     the test executable of an android build is an APK (prog/_jBuild/defaults.jam, AutoCompleteTargetName):
             `adb install -r -g <apk>`, then push the data dir to the app's external files dir
             (/sdcard/Android/data/<package>/files/dagor_test/data); the package name comes from the APK
             (`aapt2 dump packagename <apk>` from the Android SDK build tools)
  run        launch the activity with the command line the harness needs (data dir, artifact dir, result files, filters)
             as an intent extra, wait until the process is gone (`adb shell pidof <package>`), with the timeout
  exit code  `am start` doesn't report it: read the final {"event":"exit","code":N} of events.jsonl after collect()
  collect    `adb pull` the remote work dir into the host work dir
  cleanup    `adb uninstall <package>` and remove the pushed files

Missing before this can be verified: the way the engine's android startup (prog/dagorInclude/startup/dag_androidMain.inc.cpp)
receives a command line from an intent extra.
"""
import shutil
import subprocess

from .base import DeviceBackend

NOT_VERIFIED = ('the android device backend is not implemented yet: it needs a device to be verified on '
                '(see prog/tools/pythonCommon/dagorTest/devices/android.py for what it has to do)')


class AndroidDevice(DeviceBackend):
  name = 'android'
  platforms = ['android']

  def available(self) -> bool:
    if not shutil.which('adb'):
      return False
    try:
      out = subprocess.run(['adb', 'devices'], capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.SubprocessError):
      return False
    devices = [l.split('\t') for l in out.splitlines()[1:] if '\t' in l]
    return any(state == 'device' and (not self.device_id or serial == self.device_id) for serial, state in devices)

  def deploy(self, ctx, exe, data_dir, host_work_dir):
    raise NotImplementedError(NOT_VERIFIED)

  def remote_path(self, deployed, host_path):
    raise NotImplementedError(NOT_VERIFIED)

  def run(self, deployed, args, env, timeout, log_path):
    raise NotImplementedError(NOT_VERIFIED)
