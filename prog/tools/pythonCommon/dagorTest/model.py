"""Result model shared by the layers and the reports."""
import dataclasses
import enum
from typing import Dict, List, Optional


class Status(str, enum.Enum):
  PASSED = 'passed'
  FAILED = 'failed'     # a test assertion failed or the code under test crashed
  SKIPPED = 'skipped'
  TIMEOUT = 'timeout'
  ERROR = 'error'       # the test could not run: build failure, missing executable, broken harness

  # worst first; a target's status is the worst of its cases and of its own run
  @staticmethod
  def worst(statuses):
    order = [Status.ERROR, Status.TIMEOUT, Status.FAILED, Status.PASSED, Status.SKIPPED]
    statuses = list(statuses)
    for s in order:
      if s in statuses:
        return s
    return Status.SKIPPED


# exit codes of test executables, see prog/dagorInclude/unittest/dag_testEnv.h
EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_INFRA_ERROR = 2
EXIT_TIMEOUT = 3
EXIT_SKIPPED = 77


def status_from_exit_code(code: Optional[int]) -> Status:
  if code == EXIT_PASSED:
    return Status.PASSED
  if code == EXIT_SKIPPED:
    return Status.SKIPPED
  if code == EXIT_TIMEOUT:
    return Status.TIMEOUT
  if code == EXIT_INFRA_ERROR or code is None:
    return Status.ERROR
  return Status.FAILED  # EXIT_FAILED and crashes (other codes, signals)


@dataclasses.dataclass
class Artifact:
  kind: str                      # 'image' or 'file'
  name: str
  files: Dict[str, str]          # role -> path relative to the run dir ('actual', 'reference', 'diff' for images)
  passed: Optional[bool] = None
  metrics: Dict[str, float] = dataclasses.field(default_factory=dict)
  message: str = ''


@dataclasses.dataclass
class CaseResult:
  name: str
  status: Status
  duration: float = 0.0
  messages: List[str] = dataclasses.field(default_factory=list)
  location: str = ''
  artifacts: List[Artifact] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class TargetResult:
  id: str
  layer: str
  tags: List[str]
  status: Status
  duration: float = 0.0
  exit_code: Optional[int] = None
  message: str = ''              # why the target as a whole failed, was skipped or errored
  log: str = ''                  # path of the output log relative to the run dir
  attempts: int = 1
  cases: List[CaseResult] = dataclasses.field(default_factory=list)

  def counts(self):
    c = {s.value: 0 for s in Status}
    for case in self.cases:
      c[case.status.value] += 1
    return c


@dataclasses.dataclass
class RunResult:
  run_id: str
  started: str                   # ISO 8601
  duration: float
  platform: str
  arch: str
  config: str
  device: str
  git_rev: str
  command_line: List[str]
  targets: List[TargetResult]

  @property
  def status(self) -> Status:
    if not self.targets:
      return Status.SKIPPED
    return Status.worst(t.status for t in self.targets)

  def exit_code(self) -> int:
    statuses = {t.status for t in self.targets}
    if Status.ERROR in statuses:
      return 2
    if Status.FAILED in statuses or Status.TIMEOUT in statuses:
      return 1
    return 0
