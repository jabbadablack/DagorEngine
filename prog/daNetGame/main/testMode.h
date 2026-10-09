// Copyright (C) Gaijin Games KFT.  All rights reserved.
#pragma once

#include <util/dag_string.h>

namespace das
{
class Context;
}

// In-game test mode: runs daScript tests ([ecs_test] functions, see prog/daNetGameLibs/test_harness) inside the real
// game, with every game module, ECS system and template available, then exits with a test exit code
// (see unittest::ExitCode in <unittest/dag_testEnv.h>).
//
// Command line:
//   -das_test:<path>       test file or directory (recursive), named mounts allowed; repeatable
//   -test_filter:<prefix>  run only tests whose name starts with prefix; repeatable
//   -test_out:<dir>        where dastest.json (the results) and events.jsonl are written
//   -test_timeout:<sec>    per test limit, the process exits with code 3 when exceeded (default: 300)
//   -test_dt:<sec>         game time every frame advances by (default: 1/60)
//   -test_update_references  image checks replace mismatching or missing reference images
namespace test_mode
{
bool is_active();
void init();      // after settings are loaded
void update();    // main loop safe point: runs the tests once the game is ready, then requests exit
float fixed_dt(); // > 0 in test mode: every frame of the tests advances the game by exactly this time
// the game time of a frame in test mode: none until the tests run, so they start at the same game time however long
// loading took (clouds, physics), then fixed_dt()
float frame_dt();
bool is_running_test();

// API for the DngTestMode das module
void register_test(das::Context *ctx, const char *name, const char *wrapper, const char *file, int line);
void begin_case(const char *name); // sub tests; top level cases are begun by the test mode itself
void end_case();
void fail_case(bool now);
void skip_case();
void log_case(const char *msg, const char *file, int line);
void advance_frames(int count);
// expected errors (see unittest::push_logerr_expectation); expectations left open by a panicking test are closed with its case
int push_logerr_expectation(const char *substr);
int pop_logerr_expectation(int handle);
// screenshots of scenario tests: the file screencap writes for a screenshot name (screenshots{dir:t=; format:t=png} in settings)
String screenshot_path(const char *name);
// whether the 3d world is rendered (not in a menu or loading): without it screencap captures only the UI
bool renders_world();
// compares an image file with references/<name>.png next to the running test's file; returns the mismatch, empty on success
String check_image(const char *actual_file, const char *name, int channel_tolerance, float max_rms, float max_bad_pixels_percent);
} // namespace test_mode
