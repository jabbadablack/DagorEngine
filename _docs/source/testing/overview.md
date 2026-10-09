# Overview

Tests of the engine and of game projects are built and run by one tool, `test_all.py` in the engine root. Every test
*target* is declared in a `test.blk` manifest next to its sources, and belongs to one of these layers:

| Layer | What runs | Written in | Typical use |
|---|---|---|---|
| `cpp` | a Catch2 executable built with jam | C++ | engine and gameLibs code, GPU code, image output |
| `das` | daScript `[test]` functions in the das interpreter | daScript | pure game logic, daslib code |
| `ecs` | `[ecs_test]` functions inside the real game (headless dedicated server) | daScript | entity systems, templates, gameplay rules over many frames |
| `scenario` | `[ecs_test]` functions inside the rendering client | daScript | end-to-end behavior, input, screenshots compared with references |
| `exec` | any command, its exit code is the result | anything | tools with their own test harness, Python tests |

## Quick start

```bash
python test_all.py                       # build and run every engine target for this machine
python test_all.py list                  # what would run
python test_all.py run -k "engine.*"     # only targets whose id matches
python test_all.py run --project ../MyGame --no-engine
```

A project made with `new_project.py` runs its own with `python project.py test` (the same command, from the engine it
is linked to); every layer has an example target there (see [Creating a Project](../getting-started/new_project.md)).

Each run writes `_output/test_results/<run id>/` with `report.html` (open it in a browser), `junit.xml`,
`run.json` and `summary.md`, plus the full output log and artifacts of every target.
`_output/test_results/latest.txt` holds the path of the most recent run.

## Results

Every test executable, whatever the layer, reports with the same exit codes:

| Code | Meaning |
|---|---|
| 0 | all tests passed |
| 1 | a test failed (or the code under test crashed) |
| 2 | infrastructure error: the tests could not run properly |
| 3 | timeout: a test case ran longer than its limit |
| 77 | skipped: the environment can't run these tests (e.g. no GPU) |

`test_all.py` itself exits with 0 when everything passed or was skipped, 1 on failures or timeouts and 2 on errors
(build failures, broken manifests).

## Rules all layers share

- **Errors fail tests.** Anything logged with `logerr` while a test runs fails it, unless the test declares it expected
  (`unittest::ExpectLogerr` in C++, `expect_logerr` in daScript). Errors from other threads are attributed to the test
  that was running.
- **Hangs are bounded.** A per-case timeout (`caseTimeout` in `test.blk`) kills the process and reports the case that
  hung; the target `timeout` bounds the whole run.
- **Determinism.** In-game tests advance a fixed game time per frame and ignore physical input devices; image checks
  compare against checked-in references with explicit tolerances.
