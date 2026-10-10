# CI and Devices

## GitHub Actions

`.github/workflows/tests.yaml` runs on every push and pull request to `main` and on demand: on Windows, Linux and
macOS hosted runners it sets up the devtools (`make_devtools.py` answers its questions itself in CI, see
`DAGOR_NONINTERACTIVE`), then runs

```bash
python dng.py test run --gpu no -j 4 --out _output/test_results/ci --junit test-results.xml --summary-md "$GITHUB_STEP_SUMMARY"
```

Hosted runners have no GPU: GPU targets are skipped, while their `*.stub` variants run the same tests on the stub 3d
driver. The HTML report and logs are uploaded as the `test-report-<os>` artifact of the run.

In-game targets need a built game, which takes too long for every push: run them on a machine with the game built, or
in a scheduled job that builds it.

## Device backends

`--device <backend>[:<id>]` runs test executables somewhere else than the host. A backend (see
`prog/tools/pythonCommon/dagorTest/devices/base.py`) deploys the executable and its data, maps the paths the test needs
(data dir, artifact dir, result files) to device paths, runs it with a timeout and copies the outputs back. Test
executables get every path on their command line and write their exit code as the last event of `events.jsonl`, so
backends work on devices that don't report process exit codes.

| Backend | Platforms | Status |
|---|---|---|
| `local` | windows, linux, macOS | the default |
| `android` | android | skeleton, not verified on a device yet (adb) |
| `ios` | iOS | skeleton, not verified yet (simctl / devicectl) |

Backends for platforms under NDA (consoles) don't belong in the public engine: put them in your own repository and list
their directories in `DAGOR_TEST_DEVICE_PATH` (separated like `PATH`). Every `*.py` file there is loaded and its
`DeviceBackend` subclasses with a `name` become available to `--device`.
