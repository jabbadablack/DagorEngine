"""Finds test.blk manifests in the engine and in game projects."""
import os
from typing import List

from .manifest import ManifestError, Target, load_blk, load_targets, parse_project

MANIFEST_NAME = 'test.blk'
# never contain manifests, but are large
PRUNED_DIRS = {'.git', '_output', '__pycache__', '3rdPartyLibs', 'node_modules', '.test_results'}
# generated or content dirs at a project root
PRUNED_PROJECT_DIRS = {'game', 'develop', 'tools'}


def _walk_manifests(root, prune_at_root=()):
  for dirpath, dirnames, filenames in os.walk(root):
    dirnames[:] = sorted(d for d in dirnames
                         if d not in PRUNED_DIRS and not (dirpath == root and d in prune_at_root) and not d.startswith('.'))
    if MANIFEST_NAME in filenames:
      yield os.path.join(dirpath, MANIFEST_NAME)


def discover_engine(engine_root) -> List[Target]:
  targets = []
  for manifest in _walk_manifests(os.path.join(engine_root, 'prog')):
    targets += load_targets(manifest)
  return targets


def discover_project(project_root) -> List[Target]:
  project_root = os.path.abspath(project_root)
  root_manifest = os.path.join(project_root, MANIFEST_NAME)
  project = None
  if os.path.isfile(root_manifest):
    project = parse_project(load_blk(root_manifest), root_manifest)
  targets = []
  for manifest in _walk_manifests(project_root, PRUNED_PROJECT_DIRS):
    targets += load_targets(manifest, project)
  return targets


def check_unique(targets: List[Target]):
  seen = {}
  for t in targets:
    if t.id in seen:
      raise ManifestError('target {} is defined twice: {} and {}'.format(t.id, seen[t.id], t.manifest))
    seen[t.id] = t.manifest
