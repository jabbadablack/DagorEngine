//
// Dagor Engine 6.5
// Copyright (C) Gaijin Games KFT.  All rights reserved.
//
#pragma once

#include <image/dag_imageCompare.h>
#include <util/dag_string.h>

struct TexImage32;

// Test environment shared by every test layer (C++ unit tests, in-game tests).
// It is independent of the test framework: the Catch2 glue lives in <unittest/dag_unitTest.h>.
//
// Process exit codes used by all test executables:
//   0 - all tests passed, 1 - test failures, 2 - infrastructure error, 3 - timeout, 77 - skipped (e.g. no GPU)
namespace unittest
{
enum ExitCode
{
  EXIT_PASSED = 0,
  EXIT_FAILED = 1,
  EXIT_INFRA_ERROR = 2,
  EXIT_TIMEOUT = 3,
  EXIT_SKIPPED = 77,
};

struct Options
{
  String dataDir;           // test sources and reference data (absolute or relative to cwd)
  String artifactDir;       // where outputs (images, events.jsonl) are written; empty disables artifacts
  String imageVariant;      // reference image variant suffix, e.g. a driver name; empty for none
  float caseTimeoutSec = 0; // 0 disables the per-case watchdog
  bool updateReferences = false;
};

Options &options();
// Stores options with dataDir and artifactDir made absolute (relative ones are resolved against the current dir),
// so they work without engine base paths and after the current dir changes.
void set_options(const Options &opt);

// <dataDir>/rel
String data_path(const char *rel);
// <artifactDir>/<case dir>/rel, with directories created; empty if artifacts are disabled
String artifact_path(const char *rel);
// A fresh, empty, writable directory for the current test case: <artifactDir>/<case dir>/scratch, or a per-process
// directory in the system temp dir when artifacts are disabled. Each call empties it again.
String scratch_dir();

// Current test case, maintained by the test framework glue. Used to name artifact dirs and events.
void set_current_case(const char *case_name);
const char *current_case();

// Appends one JSON object line to <artifactDir>/events.jsonl and flushes it, so a crash keeps everything written before.
// fields_json is the comma-separated body of an object, without braces, e.g. "\"event\":\"caseStarted\"".
void write_event(const char *fields_json);
String json_escape(const char *s);

// Per-case watchdog: prints the hung case, records a timeout event and terminates the process with EXIT_TIMEOUT.
void start_watchdog();
void stop_watchdog();
void watchdog_case_started();
void watchdog_case_ended();

// Expected error messages. While an expectation is active, errors containing its substring are consumed instead of
// failing the test; when capture is set, consumed messages are appended to it, one per line. Thread-safe.
int push_logerr_expectation(const char *substr, String *capture = nullptr);
int pop_logerr_expectation(int handle); // returns the number of consumed messages
bool consume_expected_logerr(const char *msg);

// Errors from non-main threads cannot be reported to the framework directly; they are queued and reported on the
// main thread. Thread-safe.
void queue_unexpected_logerr(const char *msg);
bool pop_unexpected_logerr(String &out_msg);

// HTTP server provided by dng.py test to targets with requires:t="http_server" in test.blk: it serves root_dir, an empty
// writable directory where tests put the files to serve, at base_url (ends with '/'). Returns false when the server isn't
// available (e.g. the test executable is run by hand); such tests should be skipped.
bool http_service(String &out_base_url, String &out_root_dir);

struct ImageCheckResult
{
  bool passed = false;
  ImageCompareResult compare;
  String message; // human readable failure reason, empty on success
};

// Compares an image with <dataDir>/references/<name>.<imageVariant>.png, falling back to <name>.png.
// Writes actual/reference/diff images to the artifact dir and records an "image" event.
// A missing reference fails; with updateReferences the actual image becomes the reference.
ImageCheckResult check_image(const TexImage32 &actual, const char *name, const ImageCompareParams &params);
ImageCheckResult check_image_file(const char *actual_fn, const char *name, const ImageCompareParams &params);
} // namespace unittest
