# The Test Runner

`test_all.py` (engine root, implemented in `prog/tools/pythonCommon/dagorTest`) finds `test.blk` manifests, builds
what they need with jam, runs the targets in parallel and writes the reports.

## Command line

```text
python test_all.py [run|build|list|report] [options]

selection    --project DIR (repeatable)  --no-engine  --layer cpp,das,ecs,scenario,exec
             -t TAG / --exclude-tag TAG  -k GLOB (target id)  -c NAME (test case, passed to the executables)
build        --platform --arch --config (jam Platform, PlatformArch, Config; default: this machine, dev)
             --jam-arg ARG  --no-build
execution    -j N  --retries N  --timeout-scale F  --gpu auto|yes|no  --network  --update-references
             --fail-fast  --device BACKEND[:ID]
output       --out DIR  --junit FILE  --json FILE  --html FILE  --summary-md FILE  -v
```

- `build` only builds; `list` prints the selected targets; `report <run dir>` regenerates the reports of a run.
- `--gpu auto` (default) runs GPU targets, which skip themselves without a usable device; `--gpu yes` turns that skip
  into an error, `--gpu no` doesn't run them.
- GPU and `serial` targets always run alone; others run `-j` at a time.
- `--retries N` reruns failed targets; a target that passes on a retry is reported as `FLAKY` in its message.

## Manifests

A `test.blk` holds one or more targets. Engine manifests are found under `prog/`, project manifests under each
`--project` root (except its `game`, `develop` and `tools` dirs). Paths are relative to the manifest.

```text
target{
  name:t="gameLibs.foo"      // unique id, used by -k and in reports
  layer:t="cpp"              // cpp | das | ecs | scenario | exec
  tag:t="gameLibs"           // repeatable
  platform:t="windows"       // repeatable; omitted: every platform
  requires:t="http_server"   // repeatable: gpu | display | network | http_server
  timeout:r=600              // whole target, seconds (default 600)
  caseTimeout:r=60           // single test case, seconds
  serial:b=yes               // never in parallel with other targets
  args:t='--extra "quoted arg"'

  // cpp:      jamfile, exe (jam Target), dataDir (default "."), exeDir (default: the shared test OutDir)
  // das:      path (repeatable), project, isolated
  // ecs:      path (repeatable), scene, game (dedicated | client)
  // scenario: path (repeatable), scene, game (client | dedicated)
  // exec:     command, cwd, jamfile (built first), exe (a jam executable target, available as {exe})
}
```

Unknown keys, keys of another layer and duplicate ids are errors. `exec` commands may use `{python}`, `{engine}`,
`{tools}`, `{out}` (the target's output dir), `{exe}`, `{platform}`, `{arch}`, `{config}`, `{host}` and `{hostArch}`.

`requires:t="http_server"` starts an HTTP server for the target: it serves an empty writable dir, and the test reads
its URL and dir from `DAGOR_TEST_HTTP_URL` and `DAGOR_TEST_HTTP_ROOT` (`unittest::http_service` in C++).

## Reports

```text
_output/test_results/<run id>/
  report.html        everything in one file: filters, per case messages, logs, image viewer (actual/reference/diff/slider)
  junit.xml          for CI systems; image artifacts as [[ATTACHMENT|path]] lines
  run.json           the canonical result (schema 1), what `report` regenerates the others from
  summary.md         a short table, e.g. for $GITHUB_STEP_SUMMARY
  _build/            jam logs
  <target id>/       output.log, native results (junit.xml, dastest.json, events.jsonl), artifacts/
```

## Adding a test target

1. Write the tests and a `test.blk` next to them (see the layer pages).
2. `python test_all.py list -k <your id>` checks the manifest.
3. `python test_all.py run -k <your id>` builds and runs it.
