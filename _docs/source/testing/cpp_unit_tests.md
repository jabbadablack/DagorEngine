# C++ Unit Tests

C++ tests use [Catch2](https://github.com/catchorg/Catch2) (`prog/3rdPartyLibs/catch2`) with the engine's test main,
`prog/dagorInclude/unittest/mainCatch2.inc.cpp`.

## A test target

```text
prog/gameLibs/foo/tests/
  jamfile
  main.cpp
  test_foo.cpp
  test.blk
  references/        // optional: reference images
  data/              // optional: anything the tests read
```

`jamfile`: include `prog/_jBuild/unitTest.jam` instead of `defaults.jam`. It makes a console executable with
exceptions enabled, links Catch2 and the test environment (`engine/unitTest`), and puts it into
`_output/tests/<platform>-<arch>/`. Target names must be unique.

```text
Root    ?= ../../../.. ;
Location = prog/gameLibs/foo/tests ;
Target   = foo-tests ;

include $(Root)/prog/_jBuild/unitTest.jam ;

Sources = main.cpp test_foo.cpp ;
UseProgLibs += engine/memory engine/kernel engine/osApiWrappers engine/baseUtil engine/ioSys engine/math
  engine/perfMon/daProfilerStub 3rdPartyLibs/eastl gameLibs/foo ;

include $(Root)/prog/_jBuild/build.jam ;
```

`main.cpp`:

```cpp
#include <unittest/mainCatch2.inc.cpp>
```

`test.blk` (see [the test runner](test_runner.md)):

```text
target{ name:t="gameLibs.foo"; layer:t="cpp"; tag:t="gameLibs"; jamfile:t="jamfile"; exe:t="foo-tests" }
```

Tests include `<unittest/dag_unitTest.h>`, which brings the Catch2 macros, EASTL printing and the helpers below.

## Engine environment

By default only memory, the kernel and the file system are available. Define `UNITTEST_ENV` before including the main
to bring up more:

| `UNITTEST_ENV` flag | What is initialized |
|---|---|
| `UNITTEST_ENV_SETTINGS` | `settings.blk` from the data dir (`UNITTEST_SETTINGS_BLK` overrides the name) |
| `UNITTEST_ENV_CPUJOBS` | the job system |
| `UNITTEST_ENV_GPU` | settings, jobs, the 3d driver and video (window title `UNITTEST_APP_NAME`) |

```cpp
#define UNITTEST_ENV UNITTEST_ENV_GPU
#define UNITTEST_APP_NAME "fooTests"
#include <unittest/mainCatch2.inc.cpp>
```

When the 3d driver can't start the executable exits with 77 (skipped). `--gpu-driver stub` runs GPU tests on the stub
driver; tests that need real GPU results should `SKIP()` there. `CUSTOM_UNITTEST_CODE` and
`CUSTOM_UNITTEST_SHUTDOWN_CODE` add project specific setup and teardown.

## Errors and assertions

Errors logged inside a test case fail it, and so do failed `G_ASSERT`s and EASTL assertions (the code continues, as in
a release build, instead of unwinding through engine code). Fatal errors end the case. Declare errors a test provokes on
purpose:

```cpp
TEST_CASE("bad input is reported")
{
  unittest::ExpectLogerr expect("invalid header", 1); // exactly one such error, checked at scope exit
  CHECK_FALSE(parse(bad_input));
}

TEST_CASE("errors can be inspected")
{
  String errors;
  {
    unittest::CaptureLogerr capture(errors);
    run_something();
  }
  CHECK(strstr(errors, "expected text"));
}
```

## Files

| Function | Path |
|---|---|
| `unittest::data_path("x")` | the test's data dir (its source dir unless `--data-dir` is passed) |
| `unittest::artifact_path("x")` | the case's artifact dir, kept with the report |
| `unittest::scratch_dir()` | an empty writable dir for the current case |
| `unittest::http_service(url, root)` | an HTTP server for targets with `requires:t="http_server"` |

## Image checks

```cpp
CHECK_IMAGE(image, "gradient", ImageCompareParams{});           // references/gradient.png
ImageCompareParams tolerant;
tolerant.perChannelTolerance = 4;                                // a pixel is bad above this difference
tolerant.maxRms = 0.5f;                                          // whole image root mean square limit
tolerant.maxBadPixelsPercent = 0.1f;
CHECK_IMAGE(image, "lit_scene", tolerant);
```

References are looked up as `references/<name>.<variant>.png` first (the variant is the 3d driver name in GPU
tests), then `references/<name>.png`. On a mismatch the actual, reference and diff images go to the report. A missing
reference fails; `python dng.py test run --update-references` creates or replaces references with the actual images.

## Command line

Besides the Catch2 options, test executables accept `--data-dir`, `--artifact-dir`, `--case-timeout <sec>`,
`--image-variant`, `--gpu-driver` and `--update-references`. `dng.py test` passes them; run executables directly to
debug a single case:

```bash
_output/tests/windows-x86_64/foo-tests-dev.exe "my case name"
```
