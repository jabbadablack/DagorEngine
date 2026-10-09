"""Runs tests on the host: nothing to deploy, every path is already local."""
import os

from .. import process
from .base import Deployed, DeviceBackend


class LocalDevice(DeviceBackend):
  name = 'local'
  platforms = ['windows', 'linux', 'macOS']

  def available(self) -> bool:
    return True

  def deploy(self, ctx, exe, data_dir, host_work_dir):
    os.makedirs(host_work_dir, exist_ok=True)
    return Deployed(exe=exe, data_dir=data_dir, work_dir=host_work_dir, host_work_dir=host_work_dir)

  def remote_path(self, deployed, host_path):
    return host_path

  def run(self, deployed, args, env, timeout, log_path):
    full_env = dict(os.environ)
    full_env.update(env)
    return process.run([deployed.exe] + args, cwd=deployed.work_dir, log_path=log_path, timeout=timeout, env=full_env)
