"""events.jsonl written by the test environment (prog/engine/unitTest/testEnv.cpp) next to the artifacts.

It records what the native result files can't: case boundaries (to find the case a crash happened in), failures
reported outside the test thread, watchdog timeouts, infrastructure errors and image comparisons.
"""
import dataclasses
import json
import os
from typing import Dict, List, Optional

from ..model import Artifact


@dataclasses.dataclass
class Events:
  started: List[str] = dataclasses.field(default_factory=list)          # case names in start order
  ended: Dict[str, bool] = dataclasses.field(default_factory=dict)      # case name -> passed
  failures: Dict[str, List[str]] = dataclasses.field(default_factory=dict)
  timed_out_case: Optional[str] = None
  infra_errors: List[str] = dataclasses.field(default_factory=list)
  artifacts: Dict[str, List[Artifact]] = dataclasses.field(default_factory=dict)
  broken_lines: int = 0

  @property
  def unfinished_case(self) -> Optional[str]:
    """The case that was running when the process died, if any."""
    for name in reversed(self.started):
      if name not in self.ended:
        return name
    return None


def read(path: str, rel) -> Events:
  """rel maps an absolute artifact path to the path stored in the reports."""
  ev = Events()
  if not os.path.isfile(path):
    return ev
  with open(path, 'r', encoding='utf-8', errors='replace') as f:
    for line in f:
      line = line.strip()
      if not line:
        continue
      try:
        e = json.loads(line)
      except ValueError:
        ev.broken_lines += 1  # the last line of a crashed process may be cut
        continue
      kind, case = e.get('event'), e.get('case', '')
      if kind == 'caseStarted':
        ev.started.append(case)
      elif kind == 'caseEnded':
        ev.ended[case] = bool(e.get('passed'))
      elif kind == 'failure':
        ev.failures.setdefault(case, []).append(e.get('message', ''))
      elif kind == 'timeout':
        ev.timed_out_case = case
      elif kind == 'infraError':
        ev.infra_errors.append(e.get('message', ''))
      elif kind == 'image':
        files = {role: rel(e[role]) for role in ('actual', 'reference', 'diff') if e.get(role)}
        metrics = {k: float(e[k]) for k in ('rms', 'maxChannelDiff', 'badPixelsPercent') if k in e}
        ev.artifacts.setdefault(case, []).append(
          Artifact(kind='image', name=e.get('name', ''), files=files, passed=bool(e.get('passed')), metrics=metrics,
                   message=e.get('message', '')))
  return ev
