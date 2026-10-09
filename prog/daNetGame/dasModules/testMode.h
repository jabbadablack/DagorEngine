// Copyright (C) Gaijin Games KFT.  All rights reserved.
#pragma once

#include <daScript/daScript.h>
#include "main/testMode.h"
#include "net/dedicated.h"

namespace bind_dascript
{
inline void test_mode_register(const char *name, const char *wrapper, const char *file, int line, das::Context *context)
{
  test_mode::register_test(context, name ? name : "", wrapper ? wrapper : "", file ? file : "", line);
}
inline void test_mode_begin_case(const char *name) { test_mode::begin_case(name ? name : ""); }
inline void test_mode_log(const char *msg, const char *file, int line) { test_mode::log_case(msg ? msg : "", file ? file : "", line); }
inline int test_mode_push_logerr_expectation(const char *substr) { return test_mode::push_logerr_expectation(substr ? substr : ""); }
inline char *test_mode_screenshot_path(const char *name, das::Context *context, das::LineInfoArg *at)
{
  const String path = test_mode::screenshot_path(name ? name : "");
  return context->allocateString(path.c_str(), path.length(), at);
}
inline char *test_mode_check_image(const char *actual_file,
  const char *name,
  int channel_tolerance,
  float max_rms,
  float max_bad_pixels_percent,
  das::Context *context,
  das::LineInfoArg *at)
{
  const String mismatch =
    test_mode::check_image(actual_file ? actual_file : "", name ? name : "", channel_tolerance, max_rms, max_bad_pixels_percent);
  return mismatch.empty() ? nullptr : context->allocateString(mismatch.c_str(), mismatch.length(), at);
}
} // namespace bind_dascript
