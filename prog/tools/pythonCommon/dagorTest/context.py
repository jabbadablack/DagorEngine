"""Settings of one test run, shared by the build step, the layers and the reports."""
import dataclasses
import os
from typing import List, Optional


@dataclasses.dataclass
class RunContext:
  engine_root: str
  host: str                         # windows | linux | macOS
  host_arch: str
  platform: str                     # jam Platform
  arch: str                         # jam PlatformArch
  config: str                       # jam Config: dev | dbg | rel ...
  run_dir: str                      # _output/test_results/<run id>
  tools_dir: str                    # tools/dagor_cdk/<host>-<arch>
  gpu: str = 'auto'                 # auto | yes | no
  network: bool = False
  update_references: bool = False
  timeout_scale: float = 1.0
  filters: List[str] = dataclasses.field(default_factory=list)  # case name filters passed to the test executables
  jam_args: List[str] = dataclasses.field(default_factory=list)
  no_build: bool = False             # use the executables that are already built
  verbose: bool = False
  device: Optional[object] = None   # devices.base.DeviceBackend

  @property
  def output_root(self):
    """jam's _OutputRoot: $GOUT_ROOT or <engine>/_output (prog/_jBuild/defaults.jam)."""
    return os.environ.get('GOUT_ROOT') or os.path.join(self.engine_root, '_output')

  @property
  def is_windows_target(self):
    return self.platform in ('windows', 'xboxOne', 'scarlett')

  def target_dir(self, target_id):
    return os.path.join(self.run_dir, target_id)

  def rel(self, path):
    """Path relative to the run dir, with forward slashes, as stored in the reports."""
    return os.path.relpath(path, self.run_dir).replace('\\', '/')
