"""Device backends run test executables on a target device: the host itself, a phone, a console devkit.

A backend gets everything through arguments: the test executables never assume a host filesystem, they receive the data
dir, the artifact dir and the result file paths on their command line. A backend maps those host paths to device paths
(remote_path), copies inputs before the run (deploy) and outputs back after it (collect).

Backends live in this package (local, android, ios) or in directories listed in DAGOR_TEST_DEVICE_PATH, which keeps
backends for platforms under NDA (consoles) out of the public engine: each such directory holds python modules defining
a subclass of DeviceBackend with a unique `name`.
"""
import dataclasses
from typing import Dict, List, Optional

from .. import process


@dataclasses.dataclass
class Deployed:
  """A test executable and its data prepared on the device."""
  exe: str                          # device path of the executable (or the package/bundle id)
  data_dir: str                     # device path of the test data dir
  work_dir: str                     # device dir for outputs (artifacts, result files)
  host_work_dir: str                # where collect() puts the outputs on the host
  extra: Dict[str, str] = dataclasses.field(default_factory=dict)


class DeviceBackend:
  name = ''
  platforms: List[str] = []         # jam Platform values this backend runs

  def __init__(self, device_id: Optional[str] = None):
    self.device_id = device_id

  def available(self) -> bool:
    """True when a device is connected and the tooling (adb, xcrun, devkit SDK) is installed."""
    raise NotImplementedError

  def describe(self) -> str:
    return self.name + (':' + self.device_id if self.device_id else '')

  def prepare(self, ctx) -> None:
    """Called once per run before any deploy, e.g. to wake or reset the device."""

  def deploy(self, ctx, exe: str, data_dir: str, host_work_dir: str) -> Deployed:
    raise NotImplementedError

  def remote_path(self, deployed: Deployed, host_path: str) -> str:
    """Device path for a host path inside host_work_dir (result files and artifacts the test writes)."""
    raise NotImplementedError

  def run(self, deployed: Deployed, args: List[str], env: Dict[str, str], timeout: float, log_path: str) -> process.ProcessResult:
    raise NotImplementedError

  def collect(self, deployed: Deployed) -> None:
    """Copies the device work dir back to deployed.host_work_dir."""

  def cleanup(self, deployed: Deployed) -> None:
    """Removes what deploy() put on the device."""
